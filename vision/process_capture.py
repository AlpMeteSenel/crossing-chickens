"""Independent camera process; shared latest-frame slot, coherent RGB/raw metadata."""
import math,multiprocessing as mp,queue,time
from pathlib import Path
import numpy as np
from camera import CSICamera

METRICS=('dequeue_age_ms','capture_wait_ms','unpack_ms','mapped_copy_ms','requeue_ms','unpack_only_ms',
         'meter_ms','colour_ms','capture_process_ms','capture_ready_age_ms','sensor_fps','buffer_flags')

def capture_process(factory,frame_shape,raw_shape,rgb_buffer,raw_buffer,metadata,condition,controls,control_lock,stop,messages,recording_root=None):
    import cv2
    cv2.setNumThreads(1)
    rgb=np.frombuffer(rgb_buffer,np.uint8).reshape(frame_shape)
    raw=np.frombuffer(raw_buffer,np.uint16).reshape(raw_shape)
    reader=None;last_balance=0;last_warning=None;recorder=None
    try:
        reader=factory()
        if recording_root is not None:
            from local_recording import RollingCapture
            try:recorder=RollingCapture(recording_root)
            except Exception as error:print("Clean recorder unavailable:",str(error),flush=True)
        while not stop.is_set():
            with control_lock:profile,natural,ae,ag,held_exposure,held_gain,revision,white_x,white_y=controls[:]
            reader.natural_colour=bool(natural)
            reader.set_exposure_profile(('motion','balanced','lowlight')[int(profile)])
            reader.set_auto_controls(bool(ae),bool(ag),int(held_exposure),int(held_gain))
            if revision!=last_balance:
                if math.isnan(white_x):reader.rebalance()
                else:reader.set_white_reference((white_x,white_y))
                last_balance=revision
            ok,frame=reader.read()
            if not ok:raise RuntimeError('Camera capture failed')
            if recorder is not None:recorder.offer(frame,reader.timestamp)
            warning=reader.colour_warning
            if warning!=last_warning:
                try:messages.put_nowait(('warning',warning))
                except queue.Full:pass
                last_warning=warning
            timings=getattr(reader,'timings',{})
            with condition:
                np.copyto(rgb,frame);np.copyto(raw,reader.raw)
                metadata[0]+=1;metadata[1]=reader.timestamp;metadata[2]=time.monotonic()
                metadata[3]=reader.exposure;metadata[4]=reader.exposure_ms or float('nan')
                metadata[5]=reader.gain;metadata[6]=reader.gain_x
                metadata[7:10]=list(reader.gains);metadata[10]=natural
                metadata[11:11+len(METRICS)]=[timings.get(key) if timings.get(key) is not None else float('nan') for key in METRICS]
                condition.notify_all()
    except Exception as error:
        try:messages.put(('error',str(error)),timeout=.2)
        except queue.Full:pass
    finally:
        if reader is not None:reader.release()
        if recorder is not None:recorder.close()
        with condition:metadata[-1]=1;condition.notify_all()

class ProcessCamera:
    def __init__(self,factory=CSICamera,frame_shape=(616,820,3),raw_shape=(1232,1640)):
        context=mp.get_context('spawn')
        self.rgb_buffer=context.RawArray('B',math.prod(frame_shape));self.raw_buffer=context.RawArray('H',math.prod(raw_shape))
        self.metadata=context.RawArray('d',11+len(METRICS)+1)
        self.rgb=np.frombuffer(self.rgb_buffer,np.uint8).reshape(frame_shape)
        self.raw=np.frombuffer(self.raw_buffer,np.uint16).reshape(raw_shape)
        self.condition=context.Condition();self.control_lock=context.Lock()
        self.controls=context.RawArray('d',[2,1,1,1,3300,228,0,float('nan'),float('nan')])
        self.stop=context.Event();self.messages=context.Queue(maxsize=4)
        self.consumed=0;self.selected=None;self.selected_raw=None;self.warning=None;self.error=None
        self.process=context.Process(target=capture_process,args=(factory,frame_shape,raw_shape,self.rgb_buffer,self.raw_buffer,
            self.metadata,self.condition,self.controls,self.control_lock,self.stop,self.messages,
            str(Path(__file__).resolve().parent) if factory is CSICamera else None),name='IMX219-capture',daemon=True)
        self.process.start()
    def read(self):
        with self.condition:
            ready=self.condition.wait_for(lambda:self.metadata[0]!=self.consumed or self.metadata[-1],timeout=3)
            if not ready or self.metadata[0]==self.consumed:return False,None
            # Copies under the publication lock keep native ROI pixels, image and
            # timestamp together while capture continues independently afterward.
            frame=self.rgb.copy();self.selected_raw=self.raw.copy();values=list(self.metadata)
            self.consumed=values[0];self.selected_at=time.monotonic();self.selected=values
        self.read_messages()
        return True,frame
    def read_messages(self):
        while True:
            try:kind,value=self.messages.get_nowait()
            except queue.Empty:break
            if kind=='warning':self.warning=value
            else:self.error=value
    def value(self,index):return self.selected[index] if self.selected is not None else None
    @property
    def timestamp(self):return self.value(1)
    @property
    def exposure(self):return int(self.value(3)) if self.selected is not None else None
    @property
    def exposure_ms(self):
        value=self.value(4);return value if value is not None and math.isfinite(value) else None
    @property
    def gain(self):return int(self.value(5)) if self.selected is not None else None
    @property
    def gain_x(self):return self.value(6)
    @property
    def colour_warning(self):self.read_messages();return self.warning or self.error
    @property
    def timings(self):
        if self.selected is None:return {}
        result={key:value if math.isfinite(value) else None for key,value in zip(METRICS,self.selected[11:11+len(METRICS)])}
        result.update(selection_wait_ms=round((self.selected_at-self.selected[2])*1000,1),
                      selected_age_ms=round((self.selected_at-self.selected[1])*1000,1))
        return result
    @property
    def natural_colour(self):return bool(self.controls[1])
    @natural_colour.setter
    def natural_colour(self,value):
        with self.control_lock:self.controls[1]=int(bool(value))
    def set_exposure_profile(self,profile):
        if profile not in ('motion','balanced','lowlight'):raise ValueError('Unknown exposure profile')
        with self.control_lock:self.controls[0]=('motion','balanced','lowlight').index(profile)
    def set_auto_controls(self,auto_exposure=True,auto_gain=True,held_exposure=3300,held_gain=228):
        with self.control_lock:self.controls[2:6]=[int(auto_exposure),int(auto_gain),held_exposure,held_gain]
    def set_white_reference(self,point):
        with self.control_lock:self.controls[6]+=1;self.controls[7:9]=point
    def rebalance(self):
        with self.control_lock:self.controls[6]+=1;self.controls[7:9]=[float('nan'),float('nan')]
    def detail_crop(self,bounds):
        if self.selected is None:return None,None
        return CSICamera.detail_crop(self,bounds,raw=self.selected_raw,gains=np.array(self.selected[7:10]),natural=bool(self.selected[10]))
    def release(self):
        self.stop.set();self.process.join(timeout=4)
        if self.process.is_alive():self.process.terminate();self.process.join(timeout=3)
        if self.process.is_alive():raise RuntimeError('Camera process did not stop; refusing a second owner')
        self.messages.close()
