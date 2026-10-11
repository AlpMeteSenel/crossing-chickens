"""Tracking, directional line counts and calibrated ground-plane speeds.

No model or hardware dependencies: this module consumes timestamped detections.
"""
import math
from collections import Counter, deque
from dataclasses import dataclass, field

CLASSES = {'person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck'}

def points(value, count):
    if not isinstance(value, list) or len(value) != count:
        raise ValueError(f'Expected {count} points')
    result = []
    for p in value:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError('Each point must contain x and y')
        x, y = map(float, p)
        if not all(math.isfinite(v) and 0 <= v <= 1 for v in (x, y)):
            raise ValueError('Points must lie within the image')
        result.append((x, y))
    return result

def cross(a, b, c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def in_polygon(p, polygon):
    if not polygon:
        return False
    inside = False
    for a, b in zip(polygon, polygon[1:]+polygon[:1]):
        if abs(cross(a, b, p)) < 1e-9 and min(a[0], b[0])-1e-9 <= p[0] <= max(a[0], b[0])+1e-9 and min(a[1], b[1])-1e-9 <= p[1] <= max(a[1], b[1])+1e-9:
            return True
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside

def quad(value):
    q = points(value, 4)
    turns = [cross(q[i], q[(i+1)%4], q[(i+2)%4]) for i in range(4)]
    if min(abs(v) for v in turns) < 1e-5 or not (all(v > 0 for v in turns) or all(v < 0 for v in turns)):
        raise ValueError('Select four corners around a convex rectangle, without crossing edges')
    area = abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(q,q[1:]+q[:1])))/2
    if area < .002:
        raise ValueError('Selected area is too small for stable calibration')
    return q

def solve(matrix, vector):
    rows = [list(a)+[b] for a,b in zip(matrix,vector)]
    n = len(vector)
    for i in range(n):
        pivot = max(range(i,n), key=lambda j: abs(rows[j][i]))
        rows[i],rows[pivot] = rows[pivot],rows[i]
        if abs(rows[i][i]) < 1e-10:
            raise ValueError('Degenerate road calibration')
        divisor = rows[i][i]
        rows[i] = [v/divisor for v in rows[i]]
        for j in range(n):
            if j != i:
                factor = rows[j][i]
                rows[j] = [a-factor*b for a,b in zip(rows[j],rows[i])]
    return [row[-1] for row in rows]

class Calibration:
    def __init__(self, config):
        self.polygon = quad(config['points'])
        width,length = float(config['width']),float(config['length'])
        if not all(math.isfinite(v) and .1 <= v <= 1000 for v in (width,length)):
            raise ValueError('Measured sides must be between 0.1 and 1000 metres')
        matrix,vector = [],[]
        for (x,y),(u,v) in zip(self.polygon,[(0,0),(width,0),(width,length),(0,length)]):
            matrix.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
            vector.extend([u,v])
        self.h = solve(matrix,vector)
        denominators=[self.h[6]*x+self.h[7]*y+1 for x,y in self.polygon]
        self.reference_d=sum(denominators)/4
        if any(d*self.reference_d<=0 for d in denominators):raise ValueError('Calibration crosses the camera horizon')
        self.minimum_d=min(abs(d) for d in denominators)*.15
        self.maximum_world=max(100,12*width,12*length)
    def project(self, point):
        x,y = point; h = self.h; d = h[6]*x+h[7]*y+1
        # The reference rectangle sets the scale; it is not a speed-measurement ROI.
        # Reject points beyond/near the projective horizon instead of inventing speeds.
        if not math.isfinite(d) or d*self.reference_d<=0 or abs(d)<max(1e-8,self.minimum_d):
            return None
        world=((h[0]*x+h[1]*y+h[2])/d,(h[3]*x+h[4]*y+h[5])/d)
        return world if all(math.isfinite(v) and abs(v)<self.maximum_world for v in world) else None

def iou(a,b):
    area = max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    total = (a[2]-a[0])*(a[3]-a[1])+(b[2]-b[0])*(b[3]-b[1])-area
    return area/total if total else 0

@dataclass
class Track:
    id: int
    cls: str
    box: list
    conf: float
    point: tuple
    time: float
    observations: int = 1
    velocity: tuple = (0,0)
    side: int = 0
    side_point: tuple = None
    counted: bool = False
    world: deque = field(default_factory=lambda: deque(maxlen=20))
    trail: deque = field(default_factory=lambda: deque(maxlen=20))
    image_motion: deque = field(default_factory=lambda: deque(maxlen=20))

class VisionEngine:
    def __init__(self):
        self.tracks = {}; self.next_id = 1; self.key = None; self.last_frame = None
        self.counts = Counter(); self.directions = Counter(); self.events = deque(maxlen=30)
        self.line = [(0.1,.6),(.9,.6)]; self.zone = None; self.calibration = None
        self.last_ts = None; self.occupied = False; self.clear_since = None
        self.snapshot = {'tracks': [], 'counts': {}, 'directions': {}, 'occupied': False, 'inside': 0}
    def configure(self, line, zone, calibration):
        line = points(line,2)
        if math.dist(*line) < .05:
            raise ValueError('Counting line is too short')
        zone = quad(zone) if zone else None
        calibration = Calibration(calibration) if calibration else None
        self.line,self.zone,self.calibration = line,zone,calibration
        for t in self.tracks.values():
            t.world.clear(); t.side=0; t.side_point=None
        self.occupied=False; self.clear_since=None
    def reset_counts(self):
        self.counts.clear();self.directions.clear();self.events.clear()
        # Forget current tracks rather than allowing a jittering counted track to recount.
        self.tracks.clear();self.last_ts=None
    def _side(self,p):
        value = cross(*self.line,p)/math.dist(*self.line)
        return 1 if value > .012 else -1 if value < -.012 else 0
    def _count(self,t):
        side = self._side(t.point)
        if not side:
            return
        if t.side and t.side != side and not t.counted and t.observations >= 2:
            a,b = self.line; p,q = t.side_point,t.point
            dx,dy = q[0]-p[0],q[1]-p[1]
            den = dx*(b[1]-a[1])-dy*(b[0]-a[0])
            if abs(den)>1e-9:
                u = ((a[0]-p[0])*dy-(a[1]-p[1])*dx)/den
                if 0 <= u <= 1:
                    direction = 'A→B' if side == 1 else 'B→A'
                    self.counts[t.cls]+=1; self.directions[direction]+=1;t.counted=True
                    self.events.appendleft({'ts':t.time,'kind':'count','message':f'{t.cls.title()} #{t.id} crossed {direction}'})
        t.side,t.side_point = side,t.point
    def _speed(self,t):
        if self.calibration is None:
            return None,'Not calibrated'
        if self.calibration.project(t.point) is None:
            return None,'Near horizon / invalid ground projection'
        samples = list(t.world)
        if len(samples)<3 or samples[-1][0]-samples[0][0]<.5:
            return None,'Measuring…'
        mean_time=sum(p[0] for p in samples)/len(samples)
        variance=sum((p[0]-mean_time)**2 for p in samples)
        if variance<1e-8:
            return None,'Measuring…'
        slopes=[sum((p[0]-mean_time)*p[axis] for p in samples)/variance for axis in (1,2)]
        speed=3.6*math.hypot(*slopes)
        residual=0
        for axis in (1,2):
            avg=sum(p[axis] for p in samples)/len(samples)
            residual+=sum((p[axis]-avg-slopes[axis-1]*(p[0]-mean_time))**2 for p in samples)/len(samples)
        if speed > 220 or (t.cls=='person' and speed>40) or residual>.5:
            return None,'Unstable estimate'
        status='Prototype estimate' if in_polygon(t.point,self.calibration.polygon) else 'Extrapolated ground-plane estimate'
        return round(0 if speed<.5 else speed,1),status
    def update(self,frame,now):
        capture_ts=float(frame.get('capture_ts',frame.get('ts',0)))
        timestamp=float(frame.get('motion_ts',capture_ts))
        key=(frame.get('stream_id'),frame.get('src'),frame.get('w'),frame.get('h'))
        identity=(key,frame.get('frame_id'),timestamp)
        if identity==self.last_frame:
            return self.snapshot
        self.last_frame=identity
        if key!=self.key or (self.last_ts is not None and timestamp<=self.last_ts):
            self.tracks.clear();self.occupied=False;self.clear_since=None;self.key=key
        self.last_ts=timestamp
        width,height=frame.get('w',0),frame.get('h',0)
        if width<16 or height<16 or not math.isfinite(timestamp) or not math.isfinite(capture_ts) or now-capture_ts>1.5 or capture_ts>now+.3:
            return self.expire()
        kind=frame.get('source_kind','still')
        if kind not in ('live','replay','simulation'):
            return self.expire()
        dets=[]
        for d in frame.get('dets',[]):
            try:
                conf=float(d['conf']);box=[float(v) for v in d['box']]
                threshold=.25 if d.get('detail') and d['cls']=='person' else .35
                if d['cls'] not in CLASSES or not threshold<=conf<=1 or len(box)!=4 or not all(math.isfinite(v) for v in box):continue
                x1,y1,x2,y2=box
                if x2<=x1 or y2<=y1:continue
                box=[max(0,min(1,v/(width if i%2==0 else height))) for i,v in enumerate(box)]
                if box[2]<=box[0] or box[3]<=box[1]:continue
                dets.append({'cls':d['cls'],'conf':conf,'box':box,'point':((box[0]+box[2])/2,box[3])})
            except (KeyError,TypeError,ValueError):continue
        self.tracks={k:t for k,t in self.tracks.items() if timestamp-t.time<1.2}
        candidates=[]
        for tid,t in self.tracks.items():
            dt=timestamp-t.time
            predicted=(t.point[0]+t.velocity[0]*dt,t.point[1]+t.velocity[1]*dt)
            for i,d in enumerate(dets):
                if d['cls']!=t.cls:continue
                distance=math.dist(predicted,d['point']);overlap=iou(t.box,d['box'])
                gate=min(.22,.055+dt*.14+max(t.box[2]-t.box[0],t.box[3]-t.box[1])*.25)
                observed_distance=math.dist(t.point,d['point'])
                if distance<gate or (observed_distance<gate*.8 and dt<.65):
                    candidates.append((.8*distance+.2*observed_distance+.025*(1-overlap),tid,i))
        matched={};used=set()
        for _,tid,i in sorted(candidates):
            if tid not in matched and i not in used:matched[tid]=i;used.add(i)
        visible=[]
        reverse={i:tid for tid,i in matched.items()}
        for i,d in enumerate(dets):
            if i in reverse:
                t=self.tracks[reverse[i]];dt=timestamp-t.time
                if dt>1.2:t.world.clear()
                if dt>0:
                    velocity=tuple((a-b)/dt for a,b in zip(d['point'],t.point))
                    t.velocity=velocity
                t.point,t.box,t.conf,t.time=d['point'],d['box'],d['conf'],timestamp
                t.observations+=1
            else:
                t=Track(self.next_id,d['cls'],d['box'],d['conf'],d['point'],timestamp)
                self.tracks[t.id]=t;self.next_id+=1
            t.trail.append(t.point)
            t.image_motion.append((timestamp,t.point[0]*width,t.point[1]*height))
            while t.image_motion and timestamp-t.image_motion[0][0]>2.5:t.image_motion.popleft()
            self._count(t)
            world=self.calibration.project(t.point) if self.calibration else None
            if world is None:t.world.clear()
            else:
                t.world.append((timestamp,*world))
                while t.world and timestamp-t.world[0][0]>2.5:t.world.popleft()
            speed,quality=self._speed(t)
            image_speed=None
            samples=list(t.image_motion)
            if len(samples)>=3 and samples[-1][0]-samples[0][0]>=.5:
                mean_time=sum(p[0] for p in samples)/len(samples)
                variance=sum((p[0]-mean_time)**2 for p in samples)
                if variance>1e-8:
                    velocity=[sum((p[0]-mean_time)*p[axis] for p in samples)/variance for axis in (1,2)]
                    image_speed=round(math.hypot(*velocity),1)
            visible.append({'id':t.id,'cls':t.cls,'conf':t.conf,'box':t.box,'trail':list(t.trail),
                'speed_kmh':speed,'image_speed_px_s':image_speed,'speed_status':quality,'confirmed':t.observations>=2,
                'inside':t.cls=='person' and t.observations>=2 and in_polygon(t.point,self.zone)})
        inside=sum(t['inside'] for t in visible)
        # Detail detections run every other frame. Retain a recent box for display,
        # without adding invented motion samples, counts or zone occupancy.
        current_ids={t['id'] for t in visible}
        previous={t['id']:t for t in self.snapshot.get('tracks',[])}
        for tid,t in self.tracks.items():
            age=timestamp-t.time
            if tid not in current_ids and tid in previous and t.observations>=2 and 0<age<=.65:
                visible.append(dict(previous[tid],retained=True,last_seen_s=round(age,2),inside=False))
        # Hold warning through brief missed detections, but never through a stale feed.
        if inside:self.occupied=True;self.clear_since=None
        elif self.occupied:
            if self.clear_since is None:self.clear_since=timestamp
            elif timestamp-self.clear_since>=.6:self.occupied=False
        self.snapshot={'tracks':visible,'counts':dict(self.counts),'directions':dict(self.directions),
            'occupied':self.occupied,'inside':inside,'events':list(self.events),'source_kind':kind}
        return self.snapshot
    def expire(self):
        self.occupied=False;self.clear_since=None;self.tracks.clear()
        self.snapshot={'tracks':[],'counts':dict(self.counts),'directions':dict(self.directions),
            'occupied':False,'inside':0,'events':list(self.events)}
        return self.snapshot
