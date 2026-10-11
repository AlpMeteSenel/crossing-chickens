"""Ground-boundary crowd occupancy and durable, one-per-episode live warnings."""
import json,os,time,uuid,socket
from collections import deque
from datetime import datetime,timezone
from vision_engine import quad,in_polygon

DEFAULT_STOP={'mode':'crosswalk','boundary':None,'threshold':10}

def validate_stop(previous,data):
    result=dict(previous)
    if 'camera_mode' in data:
        if data['camera_mode'] not in ('crosswalk','bus_stop'):raise ValueError('Unknown camera mode')
        result['mode']=data['camera_mode']
    if 'bus_stop_boundary' in data:
        value=data['bus_stop_boundary']
        result['boundary']=[list(p) for p in quad(value)] if value is not None else None
    if 'bus_stop_threshold' in data:
        value=data['bus_stop_threshold']
        if type(value) is not int or not 1<=value<=1000:raise ValueError('Bus stop threshold must be a whole number from 1 to 1000')
        result['threshold']=value
    return result

def atomic(path,data):
    temporary=path.with_suffix('.new');temporary.write_text(json.dumps(data));temporary.replace(path)

class BusStops:
    def __init__(self,root):
        self.root=root;self.settings={s:dict(DEFAULT_STOP) for s in ('camera','simulation','replay')}
        try:
            for source,config in json.loads((root/'bus_stop_settings.json').read_text()).items():
                if source in self.settings:
                    try:self.settings[source]=validate_stop(DEFAULT_STOP,{'camera_mode':config['mode'],'bus_stop_boundary':config['boundary'],'bus_stop_threshold':config['threshold']})
                    except (ValueError,TypeError,KeyError):pass
        except (OSError,ValueError,TypeError,AttributeError):pass
        self.history=deque(maxlen=100);self.states={};self.runtime={}
        try:
            for line in (root/'bus_stop_warnings.jsonl').read_text().splitlines():
                try:
                    warning=json.loads(line)
                    if warning.get('kind')=='bus_stop_crowding' and warning.get('source_kind')=='live':self.history.appendleft(warning)
                except (ValueError,TypeError,AttributeError):pass
        except OSError:pass
        try:self.states=json.loads((root/'bus_stop_state.json').read_text())
        except (OSError,ValueError):pass
        if not isinstance(self.states,dict):self.states={}
        for source in self.settings:self.reset(source)
    def fingerprint(self,source):return json.dumps(self.settings[source],sort_keys=True)
    def reset(self,source):
        state=self.states.get(source,{})
        active=bool(state.get('active')) if isinstance(state,dict) and state.get('fingerprint')==self.fingerprint(source) else False
        self.runtime[source]={'count':None,'inside_ids':[],'pending':0,'active':active,'clear_since':None,'identity':None}
    def configure(self,source,data):
        candidate=validate_stop(self.settings[source],data)
        if candidate!=self.settings[source]:
            self.settings[source]=candidate;atomic(self.root/'bus_stop_settings.json',self.settings)
            self.states.pop(source,None);self.reset(source)
            atomic(self.root/'bus_stop_state.json',self.states)
    def pause(self,source):
        state=self.runtime[source];state['pending']=0;state['clear_since']=None;state['count']=None
        # Preserve an already-saved crowding episode across brief camera gaps.
    def valid_frame(self,frame,now):
        return bool(frame and frame.get('source_kind') in ('live','simulation','replay') and
                    frame.get('w',0)>=16 and frame.get('h',0)>=16 and not frame.get('error') and
                    0<=now-frame.get('capture_ts',0)<1.5)
    def save_active(self,source,active):
        if source=='camera':
            self.states[source]={'active':active,'fingerprint':self.fingerprint(source)}
            atomic(self.root/'bus_stop_state.json',self.states)
    def update(self,source,tracks,frame,now):
        config=self.settings[source];state=self.runtime[source]
        if config['mode']!='bus_stop' or not config['boundary'] or not self.valid_frame(frame,now) or frame.get('source_kind')!=('live' if source=='camera' else source):
            self.pause(source);return
        identity=(frame.get('stream_id'),frame.get('frame_id'))
        if identity==state['identity']:return
        state['identity']=identity
        people={t['id'] for t in tracks if t.get('cls')=='person' and t.get('confirmed') and not t.get('retained')
                and in_polygon(((t['box'][0]+t['box'][2])/2,t['box'][3]),config['boundary'])}
        state['count']=len(people)
        state['inside_ids']=sorted(people)
        if len(people)>=config['threshold']:
            state['pending']+=1;state['clear_since']=None
            if state['pending']>=2 and not state['active']:
                if source=='camera' and frame['source_kind']=='live':
                    record={'id':uuid.uuid4().hex,'ts':now,'time':datetime.fromtimestamp(now,timezone.utc).isoformat(),
                            'kind':'bus_stop_crowding','severity':'warning','message':'Bus stop threshold reached',
                            'people':len(people),'threshold':config['threshold'],'boundary':config['boundary'],
                            'node_id':socket.gethostname(),'source':source,'source_kind':'live'}
                    with (self.root/'bus_stop_warnings.jsonl').open('a') as f:
                        f.write(json.dumps(record)+'\n');f.flush();os.fsync(f.fileno())
                    self.history.appendleft(record)
                state['active']=True;self.save_active(source,True)
        else:
            state['pending']=0
            if state['active']:
                if state['clear_since'] is None:state['clear_since']=now
                elif now-state['clear_since']>=2:
                    state['active']=False;state['clear_since']=None;self.save_active(source,False)
    def snapshot(self,source,frame,now):
        config=self.settings[source];state=self.runtime[source]
        valid=self.valid_frame(frame,now)
        enabled=config['mode']=='bus_stop';count=state['count'] if valid and enabled and config['boundary'] else None
        reached=count is not None and count>=config['threshold'] and state['active']
        if not enabled:status='Crosswalk mode'
        elif not config['boundary']:status='Set the bus stop boundary'
        elif not valid:status='Waiting for fresh camera frames'
        elif count is None:status='Measuring occupancy…'
        elif reached:status='Threshold reached'
        elif count>=config['threshold']:status='Confirming threshold…'
        else:status='Below threshold'
        preview=(frame or {}).get('source_kind') in ('simulation','replay')
        return dict(config,count=count,inside_ids=state['inside_ids'] if count is not None else [],threshold_reached=reached,status=status,
                    occupancy_percent=round(count/config['threshold']*100) if count is not None else None,
                    preview=preview,warnings=list(self.history))
