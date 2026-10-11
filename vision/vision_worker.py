#!/usr/bin/env python3
"""Single camera owner; atomic timestamped detections for the integrated dashboard."""
import os,sys,time,json,base64,uuid,math,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parent
HOME=Path.home()
os.environ['YOLO_AUTOINSTALL']='false'
os.environ['YOLO_CONFIG_DIR']=str(ROOT/'yolo-config')
os.environ['OPENBLAS_NUM_THREADS']='1'
sys.path.insert(0,str(HOME/'streetmesh-benchmark/vendor'))
import cv2,numpy as np
cv2.setNumThreads(1)
from process_capture import ProcessCamera as CSICamera
from vision_detail import focus_bounds,sweep_bounds,map_crop,merge_detections
from marker_calibration import MarkerCalibration
from camera_orientation import rotate_image,rotate_point,detail_crop
from ncnn_threads import ncnn_threads

MODELS={
 'ncnn-320':str(HOME/'streetmesh-benchmark/yolo26n_320_ncnn_model'),
 'ncnn-416':str(HOME/'streetmesh-benchmark/yolo26n_416_ncnn_model'),
 'ncnn-640':str(HOME/'streetmesh-benchmark/yolo26n_640_ncnn_model'),
}
MODELS={k:v for k,v in MODELS.items() if Path(v).exists()}
def atomic(path,data):
    temporary=path.with_suffix('.new');temporary.write_text(json.dumps(data));temporary.replace(path)
def read_control():
    try:return json.loads((ROOT/'control.json').read_text())
    except (OSError,ValueError):return {'source':'camera','model':'ncnn-320'}
def simulation(t):
    image=np.full((540,900,3),(38,43,49),np.uint8)
    cv2.rectangle(image,(70,90),(830,500),(61,65,71),-1)
    for x in range(170,740,65):cv2.rectangle(image,(x,228),(x+35,305),(200,202,194),-1)
    cv2.line(image,(70,360),(830,360),(110,112,115),2)
    dets=[]
    # Known synthetic motions; no model predictions or physical street measurements.
    for index,(cls,y,period,offset,color) in enumerate([
        ('car',.78,6,0,(210,135,70)),('bicycle',.67,7,2,(80,185,110)),('person',None,14,0,(75,190,225))]):
        phase=((t+offset)%period)/period
        x=.15+.7*phase if cls!='person' else .30+.40*phase
        foot=.85-.7*phase if cls=='person' else y
        bw,bh=(.085,.12) if cls=='car' else (.035,.09)
        box=[(x-bw/2)*900,(foot-bh)*540,(x+bw/2)*900,foot*540]
        a,b,c,d=map(int,box)
        if cls=='person':
            cv2.circle(image,((a+c)//2,b+8),7,color,-1);cv2.line(image,((a+c)//2,b+15),((a+c)//2,d-5),color,5)
        else:cv2.rectangle(image,(a,b),(c,d),color,-1)
        dets.append({'cls':cls,'conf':.94,'box':box})
    cv2.putText(image,'SIMULATION - generated detections',(25,35),cv2.FONT_HERSHEY_SIMPLEX,.7,(210,220,230),2)
    return image,dets

def main():
    cap=None;active=None;model=None;model_id=None;stream=uuid.uuid4().hex
    sequence=0;next_probe=0;retry_delay=0;origin=time.monotonic();last_capture=0;fps=0;wb_revision=None
    marker=None;marker_request=None;orientation=0
    try:
        while True:
            start=time.monotonic();control=read_control();source=control.get('source','camera')
            rotation=control.get('camera_rotation',0) if source=='camera' else 0
            if rotation!=orientation:
                orientation=rotation;stream=uuid.uuid4().hex;last_capture=0;fps=0
            signature=(source,control.get('video_path'))
            if signature!=active:
                if cap:cap.release()
                cap=None;active=signature;stream=uuid.uuid4().hex;next_probe=0;origin=start
            frame=None;dets=[];error=None;kind='unavailable';src=source;capture_ts=time.time();motion_ts=None
            if source=='simulation':
                kind='simulation';frame,dets=simulation(start-origin)
            elif source=='replay':
                if cap is None:
                    path=Path(control.get('video_path','')).resolve()
                    if not path.is_relative_to((ROOT/'uploads').resolve()):raise ValueError('Replay path outside uploads')
                    cap=cv2.VideoCapture(str(path))
                ok,frame=cap.read()
                if ok:
                    kind='replay';capture_ts=time.time()
                    # Use video time for speed even if inference slows playback.
                    motion_ts=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
                    if motion_ts<=0:motion_ts=cap.get(cv2.CAP_PROP_POS_FRAMES)/max(cap.get(cv2.CAP_PROP_FPS),1)
                else:error='Replay ended; choose camera or upload another clip';frame=None
            else:
                if cap is None and start>=next_probe:
                    try:
                        sensor=any((p/'name').read_text().startswith('imx219') for p in Path('/sys/class/video4linux').glob('v4l-subdev*'))
                        if sensor:cap=CSICamera();src='IMX219 · full field'
                        else:
                            usb=next((p for p in Path('/sys/class/video4linux').glob('video*') if 'usb' in str((p/'device').resolve()).lower()),None)
                            if usb is None:raise RuntimeError('No IMX219 or USB camera found')
                            cap=cv2.VideoCapture('/dev/'+usb.name);src='USB camera'
                    except Exception as e:
                        error=f'Camera unavailable: {e}';cap=None;next_probe=start+10
                if cap is not None:
                    if isinstance(cap,CSICamera):
                        cap.natural_colour=control.get('colour','natural')=='natural'
                        cap.set_exposure_profile(control.get('exposure','lowlight'))
                        cap.set_auto_controls(control.get('auto_exposure',True),control.get('auto_gain',True),
                                              control.get('held_exposure',3300),control.get('held_gain',228))
                        if control.get('wb_revision')!=wb_revision:
                            wb_revision=control.get('wb_revision')
                            if control.get('white_point') is not None:cap.set_white_reference(rotate_point(control['white_point'],-rotation))
                            elif wb_revision is not None:cap.rebalance()
                    ok,frame=cap.read()
                    if ok:
                        kind='live';src='IMX219 · full field' if isinstance(cap,CSICamera) else 'USB camera'
                        timestamp=getattr(cap,'timestamp',None)
                        if timestamp is not None and abs(timestamp-time.monotonic())<60:
                            capture_ts=time.time()+(timestamp-time.monotonic())
                        else:capture_ts=time.time()
                    else:
                        cap.release();cap=None;frame=None;next_probe=start+10;error='Camera capture failed; retrying'
                elif error is None:error='Camera unavailable; retrying. Live detection and automatic alerts are paused.'
            if frame is not None and source=='camera':frame=rotate_image(frame,rotation)
            inference=0;detail_ran=False;focus=None;passes=0
            if frame is not None and kind!='simulation':
                try:
                    desired=control.get('model','ncnn-320')
                    if desired not in MODELS:desired=next(iter(MODELS))
                    if desired!=model_id:
                        from ultralytics import YOLO
                        model=YOLO(MODELS[desired],task='detect');model_id=desired
                        try:model.predictor=None
                        except Exception:pass
                    before=time.monotonic()
                    mode=control.get('detection_mode','crosswalk' if control.get('crosswalk_detail') else 'full')
                    images=[frame];crops=[]
                    if mode in ('tiles2','tiles4') and kind=='live':
                        for bounds in sweep_bounds(2 if mode=='tiles2' else 4,sequence):
                            if isinstance(cap,CSICamera):crop,bounds=detail_crop(cap,bounds,rotation)
                            else:
                                h,w=frame.shape[:2];x1,y1,x2,y2=bounds
                                crop=frame[int(y1*h):int(y2*h),int(x1*w):int(x2*w)]
                            if crop is not None:images.append(crop);crops.append((crop,bounds))
                    with ncnn_threads(2):
                        results=model.predict(images if crops else frame,imgsz=int(desired.rsplit('-',1)[1]),conf=.25 if crops else .35,classes=[0,1,2,3,5,7],verbose=False,device='cpu')
                    r=results[0];passes=len(images)
                    dets=[{'cls':r.names[int(c)],'conf':float(cf),'box':[float(v) for v in box]}
                        for c,cf,box in zip(r.boxes.cls,r.boxes.conf,r.boxes.xyxy) if .35<=float(cf)<=1]
                    for cr,(crop,bounds) in zip(results[1:],crops):
                        extra=[{'cls':cr.names[int(c)],'conf':float(cf),'box':[float(v) for v in box]}
                               for c,cf,box in zip(cr.boxes.cls,cr.boxes.conf,cr.boxes.xyxy)
                               if float(cf)>=(.25 if cr.names[int(c)]=='person' else .35)]
                        dets+=map_crop(extra,bounds,crop.shape,frame.shape,classes=None)
                    if crops:dets=merge_detections(dets);detail_ran=True
                    if mode=='crosswalk' and sequence%2==0 and kind=='live':
                        try:zone=control.get('bus_stop_boundary') if control.get('camera_mode')=='bus_stop' else json.loads((ROOT/'profiles.json').read_text()).get('camera',{}).get('zone')
                        except (OSError,ValueError):zone=None
                        focus=focus_bounds(zone)
                        if focus:
                            if isinstance(cap,CSICamera):crop,bounds=detail_crop(cap,focus,rotation)
                            else:
                                h,w=frame.shape[:2];x1,y1,x2,y2=focus
                                crop=frame[int(y1*h):int(y2*h),int(x1*w):int(x2*w)];bounds=focus
                            if crop is not None:
                                cr=model.predict(crop,imgsz=int(desired.rsplit('-',1)[1]),conf=.25,classes=[0],verbose=False,device='cpu')[0]
                                extra=[{'cls':'person','conf':float(cf),'box':[float(v) for v in box]} for cf,box in zip(cr.boxes.conf,cr.boxes.xyxy)]
                                dets=merge_detections(dets+map_crop(extra,bounds,crop.shape,frame.shape));detail_ran=True
                                passes+=1
                    inference=(time.monotonic()-before)*1000
                except Exception as e:
                    error=f'Model error: {e}';dets=[];kind='unavailable'
            sequence+=1;preview=None;width=height=0
            calibration_candidate=None
            request=control.get('marker_request')
            if request and kind=='live' and frame is not None:
                if request!=marker_request:marker=MarkerCalibration();marker_request=request
                calibration_candidate=marker.find(frame)
            encode_start=time.monotonic()
            if frame is not None:
                height,width=frame.shape[:2]
                ok,jpg=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,86])
                if ok:preview=base64.b64encode(jpg).decode()
                if last_capture and capture_ts>last_capture:fps=.7*fps+.3/(capture_ts-last_capture)
                last_capture=capture_ts
            encode_ms=(time.monotonic()-encode_start)*1000
            payload={'ts':time.time(),'capture_ts':capture_ts,'stream_id':stream,'frame_id':sequence,
                'src':src,'source_kind':kind,'w':width,'h':height,'fps':round(fps,1),'inference_ms':round(inference,1),
                'model':'Generated detections' if kind=='simulation' else model_id or control.get('model'),'dets':dets,'frame':preview,'error':error}
            if motion_ts is not None:payload['motion_ts']=motion_ts
            payload['camera_rotation']=rotation
            payload['colour']=control.get('colour','natural')
            payload['colour_warning']=getattr(cap,'colour_warning',None)
            payload['detail_ran']=detail_ran;payload['detail_enabled']=bool(control.get('crosswalk_detail'))
            payload['marker_request']=request;payload['calibration_candidate']=calibration_candidate
            payload['marker_status']=marker.status if request and marker else None
            payload['exposure']=control.get('exposure','lowlight')
            payload['exposure_ms']=getattr(cap,'exposure_ms',None)
            payload['exposure_lines']=getattr(cap,'exposure',None)
            payload['gain_code']=getattr(cap,'gain',None);payload['gain_x']=getattr(cap,'gain_x',None)
            payload['auto_exposure']=control.get('auto_exposure',True);payload['auto_gain']=control.get('auto_gain',True)
            payload['detection_mode']=control.get('detection_mode','full');payload['detection_passes']=passes
            payload['cpu_threads']=2
            payload['timings']=dict(getattr(cap,'timings',{}),encode_ms=round(encode_ms,1),
                                    worker_publish_age_ms=round((time.time()-capture_ts)*1000,1))
            atomic(ROOT/'vision.json',payload)
            time.sleep(max(0,.2-(time.monotonic()-start)))
    finally:
        if cap:cap.release()

def stop_worker(signum,frame):raise KeyboardInterrupt

if __name__=='__main__':
    signal.signal(signal.SIGTERM,stop_worker)
    try:main()
    except KeyboardInterrupt:pass
