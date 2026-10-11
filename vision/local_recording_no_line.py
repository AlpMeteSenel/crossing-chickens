"""Bounded local capture buffer and annotation recordings; never owns a camera.

JPEGs are muxed directly into MJPEG AVI, with no transcoding or network roundtrip.
AVI playback uses capture time; exact source timestamps are retained in a sidecar.
"""
import base64,copy,fcntl,json,math,os,queue,re,shutil,struct,threading,time,uuid
from collections import deque
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from camera_orientation import rotate_image
WINDOW=15.0
FPS=10
MIN_FREE=128*1024*1024
MAX_BUFFER_BYTES=32*1024*1024
MAX_CLIP_BYTES=512*1024*1024
MAX_CLIP_SECONDS=900
NAME=re.compile(r'^(clean|yolo)-[0-9]{8}T[0-9]{6}-[a-f0-9]{8}\.(avi|json)$')

def atomic(path,data):
    tmp=path.with_name(path.name+'.new');tmp.write_text(json.dumps(data));tmp.replace(path)

@contextmanager
def locked(directory):
    directory.mkdir(parents=True,exist_ok=True)
    with (directory/'buffer.lock').open('a') as file:
        fcntl.flock(file,fcntl.LOCK_EX)
        try:yield
        finally:fcntl.flock(file,fcntl.LOCK_UN)

def read_json(path,default):
    try:return json.loads(path.read_text())
    except (OSError,ValueError):return default

def chunk(kind,data):return kind+struct.pack('<I',len(data))+data+(b'\0' if len(data)%2 else b'')
def avi_header(width,height,fps,count,size,movi_size):
    avih=struct.pack('<14I',round(1e6/fps),size*fps,0,0x10,count,0,1,size,width,height,0,0,0,0)
    strh=struct.pack('<4s4sIHHIIIIIIIIhhhh',b'vids',b'MJPG',0,0,0,0,1,fps,0,count,size,0xffffffff,0,0,0,width,height)
    strf=struct.pack('<IiiHH4sIiiII',40,width,height,1,24,b'MJPG',width*height*3,0,0,0,0)
    stream=chunk(b'LIST',b'strl'+chunk(b'strh',strh)+chunk(b'strf',strf))
    hdrl=chunk(b'LIST',b'hdrl'+chunk(b'avih',avih)+stream)
    return b'RIFF'+struct.pack('<I',0)+b'AVI '+hdrl+b'LIST'+struct.pack('<I',movi_size)+b'movi'

class JpegAVI:
    def __init__(self,path,width,height,fps=FPS):
        self.path=Path(path);self.width=width;self.height=height;self.fps=fps
        self.file=self.path.open('w+b');self.index=[];self.maximum=0
        self.file.write(avi_header(width,height,fps,0,0,4));self.movi_start=self.file.tell()-4
        self.start=None;self.last_ts=None;self.last_jpeg=None;self.samples=[];self.closed=False
    def _append(self,jpeg):
        position=self.file.tell()-self.movi_start;self.file.write(chunk(b'00dc',jpeg))
        self.index.append(struct.pack('<4sIII',b'00dc',0x10,position,len(jpeg)));self.maximum=max(self.maximum,len(jpeg))
    def add(self,jpeg,timestamp):
        if not math.isfinite(timestamp):raise ValueError('Invalid capture timestamp')
        if self.last_ts is not None and timestamp<=self.last_ts:return False
        if self.start is None:self.start=timestamp
        slot=round((timestamp-self.start)*self.fps)
        if slot< len(self.index):return False
        if slot>MAX_CLIP_SECONDS*self.fps:raise ValueError('Recording reached its 15-minute limit')
        while len(self.index)<slot:self._append(self.last_jpeg or jpeg)
        self._append(jpeg);self.samples.append({'capture_ts':timestamp,'video_frame':len(self.index)-1})
        self.last_jpeg=jpeg;self.last_ts=timestamp
        if self.file.tell()>MAX_CLIP_BYTES:raise ValueError('Recording reached its 512 MB limit')
        return True
    def close(self):
        if self.closed:return
        self.closed=True;movi_size=self.file.tell()-self.movi_start
        self.file.write(chunk(b'idx1',b''.join(self.index)));length=self.file.tell()
        self.file.seek(0);self.file.write(avi_header(self.width,self.height,self.fps,len(self.index),self.maximum,movi_size))
        self.file.seek(4);self.file.write(struct.pack('<I',length-8));self.file.flush();self.file.close()
    def info(self):
        return {'fps':self.fps,'frames':len(self.index),'duration_seconds':round(len(self.index)/self.fps,3),
                'source_frames':len(self.samples),'capture_start':self.start,'capture_end':self.last_ts,
                'timestamps':self.samples,'timing_note':'MJPEG AVI resampled to capture time. Gaps repeat the last frame; original capture timestamps are listed.'}

class RollingCapture:
    """Copies at most10fps into a small queue; JPEG/disk work stays off capture."""
    def __init__(self,root):
        self.root=Path(root);self.directory=self.root/'recordings/rolling'
        self.queue=queue.Queue(maxsize=2);self.stop_event=threading.Event();self.next_offer=0
        self.records=deque();self.bytes=0;self.dropped=0;self.error=None;self.orientation=None;self.next_space_check=0
        self.directory.mkdir(parents=True,exist_ok=True)
        with locked(self.directory):
            for path in self.directory.glob('*.jpg'):path.unlink(missing_ok=True)
            self.publish()
        self.thread=threading.Thread(target=self.run,name='Clean-recording',daemon=True);self.thread.start()
    def offer(self,frame,monotonic_ts):
        if monotonic_ts+1e-6<self.next_offer:return
        if not self.next_offer:self.next_offer=monotonic_ts
        periods=max(1,math.floor((monotonic_ts-self.next_offer)*FPS+1e-6)+1)
        self.next_offer+=periods/FPS
        if self.queue.full():self.dropped+=1;return
        capture_ts=time.time()+monotonic_ts-time.monotonic()
        try:self.queue.put_nowait((frame.copy(),capture_ts))
        except queue.Full:self.dropped+=1
    def publish(self):
        atomic(self.directory/'buffer.json',{'frames':list(self.records),'target_fps':FPS,'window_seconds':WINDOW,
            'dropped_frames':self.dropped,'error':self.error,'rotation':self.orientation,'updated_at':time.time(),'bytes':self.bytes})
    def consume(self,frame,timestamp):
        import cv2
        now=time.monotonic()
        if now>=self.next_space_check:
            self.next_space_check=now+2
            if shutil.disk_usage(self.directory).free<MIN_FREE:raise OSError('Low disk space: clean buffer paused')
        rotation=read_json(self.root/'control.json',{}).get('camera_rotation',0)
        frame=rotate_image(frame,rotation)
        ok,jpeg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,85])
        if not ok:raise OSError('Clean frame encoding failed')
        name=uuid.uuid4().hex+'.jpg';data=jpeg.tobytes()
        with locked(self.directory):
            if rotation!=self.orientation:
                for record in self.records:(self.directory/record['name']).unlink(missing_ok=True)
                self.records.clear();self.bytes=0;self.orientation=rotation
            (self.directory/name).write_bytes(data)
            self.records.append({'name':name,'capture_ts':timestamp,'w':frame.shape[1],'h':frame.shape[0],'bytes':len(data)})
            self.bytes+=len(data)
            while self.records and (self.records[0]['capture_ts']<timestamp-WINDOW+1/FPS or self.bytes>MAX_BUFFER_BYTES or len(self.records)>200):
                record=self.records.popleft();self.bytes-=record['bytes'];(self.directory/record['name']).unlink(missing_ok=True)
            self.error=None;self.publish()
    def run(self):
        while not self.stop_event.is_set() or not self.queue.empty():
            try:frame,timestamp=self.queue.get(timeout=.2)
            except queue.Empty:continue
            try:self.consume(frame,timestamp)
            except Exception as error:
                self.error=str(error)[:160]
                try:
                    with locked(self.directory):self.publish()
                except OSError:pass
            finally:self.queue.task_done()
    def close(self):
        self.stop_event.set();self.thread.join(timeout=3)

def buffer_status(root):
    index=read_json(Path(root)/'recordings/rolling/buffer.json',{});frames=index.get('frames',[])
    age=max(0,time.time()-frames[-1]['capture_ts']) if frames else None
    span=frames[-1]['capture_ts']-frames[0]['capture_ts'] if len(frames)>1 else 0
    return {'window_seconds':WINDOW,'buffered_seconds':round(min(WINDOW,span+1/FPS),1),
            'frames':len(frames),'target_fps':FPS,'sample_fps':round((len(frames)-1)/span,1) if span else 0,
            'ready':bool(frames and age<2),'latest_age_ms':round(age*1000) if age is not None else None,
            'dropped_frames':index.get('dropped_frames',0),'error':index.get('error'),'bytes':index.get('bytes',0)}

def new_name(kind):return kind+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.avi'
def finish_clip(writer,kind,extra=None):
    writer.close()
    if not writer.index:writer.path.unlink(missing_ok=True);return None
    final=writer.path.with_suffix('');writer.path.replace(final)
    info=dict(writer.info(),name=final.name,kind=kind,created_at=time.time(),bytes=final.stat().st_size,**(extra or {}))
    atomic(final.with_suffix('.json'),info);return info

def export_clean(root):
    root=Path(root);rolling=root/'recordings/rolling';clips=root/'recordings/clips';clips.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(clips).free<MIN_FREE:raise ValueError('Not enough free storage to save footage')
    snapshot=clips/('.snapshot-'+uuid.uuid4().hex);snapshot.mkdir();writer=None
    try:
        with locked(rolling):
            index=read_json(rolling/'buffer.json',{});frames=index.get('frames',[])
            if not frames or time.time()-frames[-1]['capture_ts']>2:raise ValueError('Wait for fresh clean camera footage')
            cutoff=frames[-1]['capture_ts']-WINDOW+1/FPS
            frames=[dict(f) for f in frames if f['capture_ts']>=cutoff]
            for frame in frames:os.link(rolling/frame['name'],snapshot/frame['name'])
        first=frames[0];writer=JpegAVI(clips/(new_name('clean')+'.part'),first['w'],first['h'])
        for frame in frames:writer.add((snapshot/frame['name']).read_bytes(),frame['capture_ts'])
        return finish_clip(writer,'clean',{'rotation':index.get('rotation',0),'requested_window_seconds':WINDOW})
    except Exception:
        if writer:
            writer.close();writer.path.unlink(missing_ok=True)
        raise
    finally:shutil.rmtree(snapshot,ignore_errors=True)

def render_annotation(frame,vision):
    import cv2
    h,w=frame.shape[:2]
    colors={'person':(95,205,240),'bicycle':(120,200,85),'car':(255,170,70),'motorcycle':(160,120,245),'bus':(170,210,80),'truck':(220,170,110)}
    def poly(points,color,close=True):
        if not points:return
        import numpy as np
        pts=np.array([[round(x*w),round(y*h)] for x,y in points],dtype=np.int32)
        cv2.polylines(frame,[pts],close,color,2)
    bus=vision.get('camera_mode')=='bus_stop';profile=vision.get('profile') or {}
    poly((vision.get('bus_stop') or {}).get('boundary') if bus else profile.get('zone'),(220,185,110) if bus else (180,210,95))
    for track in vision.get('tracks',[]):
        color=colors.get(track.get('cls'),(255,255,255));a,b,c,d=track['box']
        x1,y1,x2,y2=round(a*w),round(b*h),round(c*w),round(d*h)
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2);poly(track.get('trail'),color,False)
        label=f"{track['cls']} #{track['id']}"+(' (recent)' if track.get('retained') else '')+f" | {round(track['conf']*100)}%"
        if track.get('speed_kmh') is not None:label+=f" | ~{track['speed_kmh']:.1f} km/h"
        elif track.get('image_speed_px_s') is not None:label+=f" | {track['image_speed_px_s']:.1f} px/s"
        (width,height),baseline=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,.45,1)
        x=max(0,min(x1,w-width-8));y=max(height+8,min(y1,h-2))
        cv2.rectangle(frame,(x,y-height-6),(min(w,x+width+8),y+baseline),(20,24,28),-1)
        cv2.putText(frame,label,(x+4,y-3),cv2.FONT_HERSHEY_SIMPLEX,.45,color,1,cv2.LINE_AA)
    return frame

class AnnotatedRecording:
    def __init__(self,root):
        self.root=Path(root);self.directory=self.root/'recordings/clips';self.directory.mkdir(parents=True,exist_ok=True)
        self.lock=threading.Lock();self.queue=queue.Queue(maxsize=2);self.active=False;self.finishing=False
        self.writer=None;self.error=None;self.last_file=None;self.session=None;self.dropped=0;self.first=None;self.rotation=None
        self.thread=None;self.started_at=None
    def start(self):
        with self.lock:
            if self.active or self.finishing or self.thread and self.thread.is_alive():raise ValueError('A recording is already active or finishing')
            if shutil.disk_usage(self.directory).free<MIN_FREE:raise ValueError('Not enough free storage to record')
            self.active=True;self.error=None;self.first=None;self.rotation=None;self.started_at=time.time();self.dropped=0;self.session=uuid.uuid4().hex
            self.thread=threading.Thread(target=self.run,name='YOLO-recording',daemon=True);self.thread.start()
        return self.status()
    def stop(self,reason=None):
        with self.lock:
            self.active=False
            self.finishing=bool(self.thread and self.thread.is_alive())
            if reason:self.error=reason
        return self.status()
    def feed(self,camera,vision):
        if not self.active or camera.get('source_kind')!='live' or not camera.get('frame'):return
        age=time.time()-camera.get('capture_ts',0)
        if not 0<=age<1.5:return
        try:self.queue.put_nowait((self.session,dict(camera),copy.deepcopy(vision)))
        except queue.Full:self.dropped+=1
    def run(self):
        import cv2,numpy as np
        writer=None;last_seen=time.monotonic();recording_rotation=None
        try:
            while self.active or not self.queue.empty():
                try:session,camera,vision=self.queue.get(timeout=.2)
                except queue.Empty:
                    if self.active and time.monotonic()-last_seen>5:self.stop('Recording stopped: no fresh YOLO frames')
                    continue
                try:
                    if session!=self.session:continue
                    last_seen=time.monotonic()
                    if shutil.disk_usage(self.directory).free<MIN_FREE:raise ValueError('Recording stopped: low disk space')
                    frame=cv2.imdecode(np.frombuffer(base64.b64decode(camera['frame']),np.uint8),cv2.IMREAD_COLOR)
                    if frame is None:raise ValueError('Invalid YOLO preview frame')
                    rotation=camera.get('camera_rotation',0)
                    if writer is None:
                        writer=JpegAVI(self.directory/(new_name('yolo')+'.part'),frame.shape[1],frame.shape[0])
                        with self.lock:self.writer=writer;self.first=camera['capture_ts'];self.rotation=rotation
                        recording_rotation=rotation
                    if (frame.shape[1],frame.shape[0])!=(writer.width,writer.height) or rotation!=recording_rotation:
                        raise ValueError('Recording stopped: camera orientation or size changed')
                    render_annotation(frame,vision)
                    ok,jpeg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,85])
                    if not ok:raise ValueError('Annotated frame encoding failed')
                    writer.add(jpeg.tobytes(),camera['capture_ts'])
                finally:self.queue.task_done()
        except Exception as error:
            with self.lock:self.error=str(error)[:180];self.active=False
        finally:
            with self.lock:self.active=False;self.finishing=True
            try:
                if writer:
                    info=finish_clip(writer,'yolo',{'rotation':recording_rotation,'dropped_input_frames':self.dropped})
                    if info:self.last_file=info['name']
            except Exception as error:
                with self.lock:self.error='Unable to finalize recording: '+str(error)[:140]
            finally:
                while not self.queue.empty():
                    try:self.queue.get_nowait();self.queue.task_done()
                    except queue.Empty:break
                with self.lock:self.writer=None;self.finishing=False
    def status(self):
        with self.lock:
            writer=self.writer
            return {'active':self.active,'finishing':self.finishing,'seconds':round(len(writer.index)/FPS,1) if writer else 0,
                    'frames':len(writer.index) if writer else 0,'dropped_frames':self.dropped,'error':self.error,'last_file':self.last_file}
    def close(self):
        self.stop()
        if self.thread:self.thread.join(timeout=4)

def list_clips(root):
    directory=Path(root)/'recordings/clips';result=[]
    for path in directory.glob('*.avi'):
        if not NAME.fullmatch(path.name):continue
        info=read_json(path.with_suffix('.json'),{})
        if info.get('name')!=path.name:continue
        result.append({key:info.get(key) for key in ('name','kind','created_at','bytes','duration_seconds','source_frames','fps')})
    return sorted(result,key=lambda r:r.get('created_at') or 0,reverse=True)[:30]

def download_path(root,name):
    if not NAME.fullmatch(name):raise ValueError('Unknown recording file')
    directory=(Path(root)/'recordings/clips').resolve();path=directory/name
    if not path.is_file() or path.is_symlink() or path.resolve().parent!=directory:raise ValueError('Recording not found')
    return path
