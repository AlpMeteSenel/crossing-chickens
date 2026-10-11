"""IMU orientation monitoring and tamper alerts."""
import math,uuid
from collections import deque
class TamperMonitor:
    def __init__(self):self.baseline=None;self.samples=[];self.hits=0;self.last_alert=0;self.events=deque(maxlen=20)
    def update(self,s,now):
        try:a=[float(s[k]) for k in ('ax','ay','az')];r=[float(s[k]) for k in ('gx','gy','gz')]
        except (KeyError,ValueError,TypeError):return
        norm=math.sqrt(sum(v*v for v in a))
        if not all(math.isfinite(v) for v in a+r) or norm<.05:return
        a=[v/norm for v in a]
        if self.baseline is None:
            self.samples.append((a,r))
            if len(self.samples)<10:return
            average=[sum(x[0][i] for x in self.samples)/len(self.samples) for i in range(3)];n=math.sqrt(sum(v*v for v in average))
            if n<.8:self.samples=[];return
            self.baseline=([v/n for v in average],r);return
        b,angles=self.baseline;tilt=math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))))));rotation=max(abs((x-y+180)%360-180) for x,y in zip(r,angles))
        self.hits=self.hits+1 if tilt>=12 or rotation>=15 else 0
        if self.hits>=3 and now-self.last_alert>=30:
            self.last_alert=now;self.events.append({'id':uuid.uuid4().hex,'kind':'camera_tamper','message':'Camera moved or tilted','ts':now,'severity':'warning','tilt_deg':round(tilt,1),'rotation_deg':round(rotation,1)})
