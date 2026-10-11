"""Continuously drain the camera while inference consumes the latest coherent frame."""
import threading,time
from camera import CSICamera

class LiveCamera:
    def __init__(self,factory=CSICamera):
        self.reader=factory();self.condition=threading.Condition();self.stop=threading.Event()
        self.latest=None;self.selected=None;self.consumed=0;self.sequence=0;self.done=False;self.error=None
        self.natural_colour=True;self.exposure_profile='lowlight';self.balance_request=None;self.balance_revision=0
        self.auto_controls=(True,True,3300,228)
        self.thread=threading.Thread(target=self._capture,name='IMX219-capture',daemon=True);self.thread.start()
    def _capture(self):
        applied_balance=0
        try:
            while not self.stop.is_set():
                with self.condition:
                    profile=self.exposure_profile;natural=self.natural_colour
                    auto_controls=self.auto_controls
                    revision=self.balance_revision;request=self.balance_request
                self.reader.natural_colour=natural;self.reader.set_exposure_profile(profile)
                self.reader.set_auto_controls(*auto_controls)
                if revision!=applied_balance:
                    if request is None:self.reader.rebalance()
                    else:self.reader.set_white_reference(request)
                    applied_balance=revision
                ok,frame=self.reader.read()
                if not ok:raise RuntimeError('Camera capture failed')
                self.sequence+=1
                packet={'sequence':self.sequence,'frame':frame,'timestamp':self.reader.timestamp,
                        'raw':self.reader.raw,'gains':self.reader.gains.copy(),'natural':natural,
                        'exposure':self.reader.exposure,'exposure_ms':self.reader.exposure_ms,
                        'gain':self.reader.gain,'gain_x':self.reader.gain_x,
                        'auto_exposure':auto_controls[0],'auto_gain':auto_controls[1],
                        'timings':dict(getattr(self.reader,'timings',{})),'ready_at':time.monotonic(),
                        'colour_warning':self.reader.colour_warning}
                with self.condition:self.latest=packet;self.condition.notify_all()
        except Exception as e:
            with self.condition:self.error=str(e)
        finally:
            self.reader.release()
            with self.condition:self.done=True;self.condition.notify_all()
    def read(self):
        with self.condition:
            ready=self.condition.wait_for(lambda:self.done or self.latest is not None and self.latest['sequence']!=self.consumed,timeout=3)
            if not ready or self.latest is None or self.latest['sequence']==self.consumed:return False,None
            self.selected=self.latest;self.consumed=self.selected['sequence']
            self.selected_at=time.monotonic()
            return True,self.selected['frame']
    @property
    def timestamp(self):return self.selected['timestamp'] if self.selected else None
    @property
    def exposure(self):return self.selected['exposure'] if self.selected else None
    @property
    def exposure_ms(self):return self.selected['exposure_ms'] if self.selected else None
    @property
    def gain(self):return self.selected['gain'] if self.selected else None
    @property
    def gain_x(self):return self.selected['gain_x'] if self.selected else None
    @property
    def timings(self):
        if self.selected is None:return {}
        return dict(self.selected['timings'],selection_wait_ms=round((self.selected_at-self.selected['ready_at'])*1000,1),
                    selected_age_ms=round((self.selected_at-self.selected['timestamp'])*1000,1))
    @property
    def colour_warning(self):return self.selected['colour_warning'] if self.selected else self.error
    def set_exposure_profile(self,profile):
        if profile not in ('motion','balanced','lowlight'):raise ValueError('Unknown exposure profile')
        with self.condition:self.exposure_profile=profile
    def set_auto_controls(self,auto_exposure=True,auto_gain=True,held_exposure=3300,held_gain=228):
        with self.condition:self.auto_controls=(auto_exposure,auto_gain,held_exposure,held_gain)
    def set_white_reference(self,point):
        with self.condition:self.balance_request=point;self.balance_revision+=1
    def rebalance(self):
        with self.condition:self.balance_request=None;self.balance_revision+=1
    def detail_crop(self,bounds):
        packet=self.selected
        if packet is None:return None,None
        return self.reader.detail_crop(bounds,raw=packet['raw'],gains=packet['gains'],natural=packet['natural'])
    def release(self):
        self.stop.set();self.thread.join(timeout=6)
        if self.thread.is_alive():raise RuntimeError('Camera thread did not stop; refusing a second camera owner')
