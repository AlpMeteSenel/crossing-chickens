#!/usr/bin/env python3
"""Existing sensor dashboard plus tracked vision and crossing LED automation."""
import asyncio,json,time,uuid,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from aiohttp import web
from motion_security import TamperMonitor
from vision_engine import VisionEngine,quad,points
from auto_camera import validate_controls
from camera_orientation import validate_rotation,rotate_points
from local_recording import AnnotatedRecording,buffer_status,export_clean,list_clips,download_path
from bus_stop import BusStops,validate_stop
from led_effects import DEFAULT as LED_DEFAULT,KEYS as LED_KEYS,validate_effects,restore_effects,rpc_args

ROOT=Path(__file__).resolve().parent
SIM_PROFILE={'line':[[.50,.2],[.50,.91]],'zone':[[.40,.38],[.60,.38],[.60,.58],[.40,.58]],
    'calibration':{'points':[[.08,.15],[.92,.15],[.92,.93],[.08,.93]],'width':20,'length':12}}
DEFAULT={'line':[[.1,.6],[.9,.6]],'zone':None,'calibration':None}
def atomic(path,data):
    p=path.with_suffix('.new');p.write_text(json.dumps(data));p.replace(path)

class Hub:
    def __init__(self,bridge_factory=None):
        self.tamper=TamperMonitor();self.engine=VisionEngine();self.clients=set();self.bridge_factory=bridge_factory
        self.pool=ThreadPoolExecutor(max_workers=1);self.bridge=None
        self.control={'source':'camera','model':'ncnn-320','colour':'natural','exposure':'lowlight',
                      'auto_exposure':True,'auto_gain':True,'held_exposure':3300,'held_gain':228,'detection_mode':'full','camera_rotation':0}
        try:
            saved=json.loads((ROOT/'control.json').read_text())
            if saved.get('model') in ('ncnn-320','ncnn-416','ncnn-640'):self.control['model']=saved['model']
            if saved.get('colour') in ('natural','neutral'):self.control['colour']=saved['colour']
            if saved.get('exposure') in ('motion','balanced','lowlight'):self.control['exposure']=saved['exposure']
            self.control['crosswalk_detail']=bool(saved.get('crosswalk_detail',False))
            self.control.update(validate_controls(saved))
            self.control['camera_rotation']=validate_rotation(saved.get('camera_rotation',0))
            mode=saved.get('detection_mode','crosswalk' if saved.get('crosswalk_detail') else 'full')
            if mode in ('full','crosswalk','tiles2','tiles4'):self.control['detection_mode']=mode
            for key in ('white_point','wb_revision','marker_request'):
                if key in saved:self.control[key]=saved[key]
        except (OSError,ValueError,TypeError):pass
        self.profiles={'camera':dict(DEFAULT),'simulation':SIM_PROFILE,'replay':dict(DEFAULT)}
        try:self.profiles.update(json.loads((ROOT/'profiles.json').read_text()))
        except (OSError,ValueError):pass
        self.engine.configure(**self.profiles['camera'])
        self.auto_led=False;self.manual=None;self.manual_revision=0;self.applied_revision=0
        self.auto_applied=False;self.led_signature=None;self.command_latency=None;self.mode_confirmed_latency=None
        self.last_command=None;self.error=None;self.sensors=None;self.mcu_ok=False;self.last_mcu=0
        self.brightness=10;self.brightness_applied=None
        try:
            saved=json.loads((ROOT/'led_settings.json').read_text()).get('brightness',10)
            if type(saved) is int and 0<=saved<=100:self.brightness=saved
        except (OSError,ValueError,TypeError,AttributeError):pass
        self.effects=dict(LED_DEFAULT);self.effects_applied=None;self.led_status=None
        try:
            settings=json.loads((ROOT/'led_settings.json').read_text()).get('effects',{})
            self.effects=restore_effects(settings)
        except (OSError,ValueError,TypeError,AttributeError):pass
        self.frame=None;self.vision=None;self.last_vision_identity=None
        self.calibration_message=None
        self.recording=AnnotatedRecording(ROOT)
        self.bus_stops=BusStops(ROOT)
        self.sync_stop_mode()
        try:
            enabled=json.loads((ROOT/'led_settings.json').read_text()).get('auto_led',False) is True
            self.auto_led=enabled and self.control['source']=='camera' and self.control['camera_mode']=='crosswalk' and bool(self.engine.zone)
        except (OSError,ValueError,TypeError,AttributeError):pass
        atomic(ROOT/'control.json',self.control)
    def save_led_settings(self):
        atomic(ROOT/'led_settings.json',{'brightness':self.brightness,'effects':self.effects,'auto_led':self.auto_led})
    def sync_stop_mode(self):
        config=self.bus_stops.settings[self.control['source']]
        self.control['camera_mode']=config['mode'];self.control['bus_stop_boundary']=config['boundary']
    def configure_stop(self,data):
        self.bus_stops.configure(self.control['source'],data);self.sync_stop_mode()
        if self.control['camera_mode']=='bus_stop':
            self.auto_led=False;self.save_led_settings()
        atomic(ROOT/'control.json',self.control)
    def configure(self,data):
        previous=self.profiles[self.control['source']]
        candidate={key:data.get(key,previous.get(key)) for key in ('line','zone','calibration')}
        self.engine.configure(**candidate)
        self.profiles[self.control['source']]=candidate
        atomic(ROOT/'profiles.json',self.profiles)
        if not candidate['zone']:
            self.auto_led=False;self.save_led_settings()
    def rotate_camera(self,rotation):
        rotation=validate_rotation(rotation)
        previous=self.control.get('camera_rotation',0)
        if rotation==previous:return
        self.recording.stop('Recording stopped: camera rotation changed')
        delta=(rotation-previous)%360
        profile=dict(self.profiles['camera'])
        for key in ('line','zone'):profile[key]=rotate_points(profile.get(key),delta)
        if profile.get('calibration'):
            profile['calibration']=dict(profile['calibration'],points=rotate_points(profile['calibration']['points'],delta))
        self.profiles['camera']=profile
        atomic(ROOT/'profiles.json',self.profiles)
        stop=self.bus_stops.settings['camera']
        self.bus_stops.configure('camera',{'bus_stop_boundary':rotate_points(stop['boundary'],delta)})
        if self.control.get('white_point') is not None:
            self.control['white_point']=rotate_points([self.control['white_point']],delta)[0]
        self.control['camera_rotation']=rotation
        self.control.pop('marker_request',None)
        self.sync_stop_mode()
        self.engine.tracks.clear();self.engine.expire();self.engine.last_ts=None
        self.engine.configure(**self.profiles[self.control['source']])
        self.frame=None;self.last_vision_identity=None
        self.calibration_message='Camera rotated. Saved zones and ground calibration rotated with the image. Recalibrate if you physically move the camera.'
        atomic(ROOT/'control.json',self.control)
    def select_source(self,source,video_path=None):
        if source not in ('camera','simulation','replay'):raise ValueError('Unknown source')
        if source=='replay' and not (video_path or self.control.get('video_path')):raise ValueError('Upload a video first')
        self.recording.stop('Recording stopped: camera source changed')
        self.auto_led=False;self.save_led_settings();self.control['source']=source
        if video_path:self.control['video_path']=str(video_path)
        self.engine.configure(**self.profiles[source]);self.engine.reset_counts();self.engine.expire()
        self.last_vision_identity=None;self.frame=None
        self.sync_stop_mode()
        atomic(ROOT/'control.json',self.control)
    def fresh_live(self,now=None):
        now=now or time.time();f=self.frame or {}
        return self.control['source']=='camera' and f.get('source_kind')=='live' and 0<=now-f.get('capture_ts',0)<1.5 and f.get('w',0)>=16 and f.get('h',0)>=16 and not f.get('error')
    def desired_auto(self):
        if not self.auto_led or self.control.get('camera_mode')=='bus_stop':return None
        if self.fresh_live() and self.engine.zone and self.engine.snapshot.get('occupied'):
            return ('set_mode',(11,))
        return ('set_led',(0,0,0))
    async def rpc(self,name,*args):
        loop=asyncio.get_running_loop()
        def invoke():
            if self.bridge is None:
                if self.bridge_factory:self.bridge=self.bridge_factory()
                else:
                    from arduino.router_bridge import Bridge
                    self.bridge=Bridge('unix:///run/arduino-router.sock');self.bridge.connect()
            return self.bridge.call(name,*args,timeout=1.5)
        return await loop.run_in_executor(self.pool,invoke)
    def payload(self):
        now=time.time();f=self.frame
        age=max(0,(now-f.get('capture_ts',now))*1000) if f else None
        profile=self.profiles[self.control['source']]
        v=dict(self.engine.snapshot);v['events']=list(v.get('events',[]))+list(self.tamper.events);v['power_state']=(f or {}).get('power_state','active')
        v.update(profile=profile,auto_led=self.auto_led,live=self.fresh_live(now),
            frame_age_ms=round(age) if age is not None else None,
            command_latency_ms=self.command_latency,mode_confirmed_ms=self.mode_confirmed_latency,
            led_command=self.last_command,model=self.control['model'],source=self.control['source'],
            colour=self.control.get('colour','natural'),
            exposure=self.control.get('exposure','lowlight'),
            auto_exposure=self.control.get('auto_exposure',True),auto_gain=self.control.get('auto_gain',True),
            detection_mode=self.control.get('detection_mode','full'),
            crosswalk_detail=self.control.get('crosswalk_detail',False),
            camera_mode=self.control.get('camera_mode','crosswalk'),
            camera_rotation=self.control.get('camera_rotation',0),
            bus_stop=self.bus_stops.snapshot(self.control['source'],f,now),
            marker_searching=bool(self.control.get('marker_request')),
            calibration_message=(f or {}).get('marker_status') if self.control.get('marker_request') and (f or {}).get('marker_request')==self.control.get('marker_request') else self.calibration_message,
            crossing_status='No crossing zone' if not profile['zone'] else 'Pedestrian crossing' if v.get('occupied') else 'Crossing clear')
        if not f or f.get('source_kind')=='unavailable' or age is None or age>1500:
            v['crossing_status']='Live evaluation unavailable';v['tracks']=[];v['occupied']=False
        return {'ts':now,'mcu_ok':self.mcu_ok,'mcu_age_s':round(now-self.last_mcu,1) if self.last_mcu else None,
            'err':self.error,'sensors':self.sensors,'camera':f,'vision':v,
            'recording':{'clean':buffer_status(ROOT),'annotated':self.recording.status()},
            'led':{'brightness_percent':self.brightness,'applied_percent':self.brightness_applied,'effects':self.effects,
                   'effects_applied':self.effects_applied,'status':self.led_status}}
    async def vision_loop(self):
        while True:
            try:
                frame=json.loads((ROOT/'vision.json').read_text())
                identity=(frame.get('stream_id'),frame.get('frame_id'))
                source_matches=frame.get('source_kind') in ({'live','idle','unavailable'} if self.control['source']=='camera' else {self.control['source']})
                if self.control['source']=='camera':source_matches=source_matches and frame.get('camera_rotation',0)==self.control.get('camera_rotation',0)
                if not source_matches:
                    self.frame=None;self.engine.expire()
                elif identity!=self.last_vision_identity:
                    self.last_vision_identity=identity;self.frame=frame
                    if self.control.get('marker_request') and frame.get('marker_request')==self.control['marker_request'] and frame.get('calibration_candidate') and self.fresh_live():
                        try:
                            self.configure({'calibration':frame['calibration_candidate']})
                            self.control.pop('marker_request',None);atomic(ROOT/'control.json',self.control)
                            self.calibration_message='Printed marker calibration saved. Remove the marker; keep camera fixed.'
                        except ValueError as e:self.calibration_message=str(e)
                    self.engine.update(frame,time.time())
                    self.bus_stops.update(self.control['source'],self.engine.snapshot.get('tracks',[]),frame,time.time())
                    if self.fresh_live():self.recording.feed(frame,self.payload()['vision'])
                if time.time()-frame.get('capture_ts',0)>1.5 or frame.get('source_kind')=='unavailable':
                    self.engine.expire();self.bus_stops.pause(self.control['source'])
            except (OSError,ValueError,TypeError):
                if self.frame is None or time.time()-self.frame.get('capture_ts',0)>1.5:
                    self.engine.expire();self.bus_stops.pause(self.control['source'])
            data=json.dumps(self.payload())
            for ws in list(self.clients):
                try:await ws.send_str(data)
                except Exception:self.clients.discard(ws)
            await asyncio.sleep(.10)
    async def hardware_loop(self):
        next_sensor=0;next_led_status=0
        while True:
            try:
                if self.brightness_applied!=self.brightness:
                    requested=self.brightness
                    result=await self.rpc('set_brightness',requested)
                    if result is not True:raise RuntimeError('MCU rejected brightness command')
                    self.brightness_applied=requested
                if self.effects_applied!=self.effects:
                    requested=dict(self.effects)
                    result=await self.rpc('set_effect_config',*rpc_args(requested))
                    if result is not True:raise RuntimeError('MCU rejected animation settings')
                    self.effects_applied=requested
                command=None;revision=None;automatic=False
                if self.manual_revision!=self.applied_revision:
                    command=self.manual;revision=self.manual_revision
                else:
                    desired=self.desired_auto()
                    if desired is not None and desired!=self.led_signature:command=desired;automatic=True
                    elif desired is None and self.auto_applied:command=('set_led',(0,0,0))
                if command:
                    name,args=command;start=time.time()
                    frame_ts=(self.frame or {}).get('capture_ts',start)
                    result=await self.rpc(name,*args)
                    if result is not True:raise RuntimeError('MCU rejected LED command')
                    self.led_signature=command;self.auto_applied=automatic
                    if revision is not None:self.applied_revision=revision
                    self.last_command={'method':name,'args':list(args),'at':time.time(),'ack_ms':round((time.time()-start)*1000,1),'automatic':automatic}
                    self.command_latency=round((time.time()-frame_ts)*1000,1) if automatic and self.fresh_live() else None
                    self.mode_confirmed_latency=None
                if time.monotonic()>=next_sensor:
                    sensor=await self.rpc('read_sensors')
                    if isinstance(sensor,(str,bytes)):sensor=json.loads(sensor)
                    if not isinstance(sensor,dict):raise ValueError('Invalid sensor response')
                    sensor['_received_at']=time.time();atomic(ROOT/'sensor-state.json',sensor);self.tamper.update(sensor,time.time());self.sensors=sensor;self.mcu_ok=True;self.last_mcu=time.time();self.error=None
                    if self.last_command and self.mode_confirmed_latency is None:
                        expected=self.last_command['args'][0] if self.last_command['method']=='set_mode' else 10
                        if sensor.get('led_mode')==expected:self.mode_confirmed_latency=round((time.time()-self.last_command['at'])*1000,1)
                    next_sensor=time.monotonic()+.2
                if time.monotonic()>=next_led_status:
                    status=await self.rpc('led_status')
                    if isinstance(status,(str,bytes)):status=json.loads(status)
                    if isinstance(status,dict):self.led_status=status
                    next_led_status=time.monotonic()+1
            except Exception as e:
                self.mcu_ok=False;self.error=str(e)[:180]
                failed=self.bridge;self.bridge=None
                if failed is not None and hasattr(failed,'disconnect'):
                    try:await asyncio.get_running_loop().run_in_executor(self.pool,failed.disconnect)
                    except Exception:pass
                self.led_signature=None;self.brightness_applied=None;self.effects_applied=None
                await asyncio.sleep(.25)
            await asyncio.sleep(.04)
    def manual_command(self,command):
        self.auto_led=False;self.save_led_settings();self.manual=command;self.manual_revision+=1
    async def websocket(self,request):
        ws=web.WebSocketResponse(heartbeat=20);await ws.prepare(request);self.clients.add(ws)
        try:
            async for msg in ws:
                if msg.type==web.WSMsgType.TEXT:
                    try:
                        data=json.loads(msg.data)
                        if 'mode' in data:
                            mode=data['mode']
                            if type(mode) is not int or not 0<=mode<=33:raise ValueError('Unknown animation')
                            # Keep the dashboard Off command compatible with older firmware.
                            self.manual_command(('set_led',(0,0,0)) if mode==6 else ('set_mode',(mode,)))
                        if 'led' in data:
                            led=data['led']
                            if not isinstance(led,list) or len(led)!=3:raise ValueError('RGB requires three channels')
                            self.manual_command(('set_led',tuple(max(0,min(255,int(v))) for v in led)))
                    except (ValueError,TypeError) as e:await ws.send_json({'error':str(e)})
        finally:self.clients.discard(ws)
        return ws

def make_app(hub):
    app=web.Application(client_max_size=100*1024*1024)
    async def index(request):return web.FileResponse(ROOT/'dashboard.html')
    async def state(request):return web.json_response(hub.payload())
    async def configure(request):
        try:
            data=await request.json()
            if 'auto_led' in data and type(data['auto_led']) is not bool:raise ValueError('Automatic LEDs needs true or false')
            effect_candidate=validate_effects(hub.effects,data)
            if 'brightness' in data and (type(data['brightness']) is not int or not 0<=data['brightness']<=100):raise ValueError('Brightness must be an integer from 0 to 100%')
            camera_settings=validate_controls(data)
            if 'camera_rotation' in data:validate_rotation(data['camera_rotation'])
            stop_source=data.get('source',hub.control['source'])
            if stop_source not in hub.profiles:raise ValueError('Unknown source')
            stop_candidate=validate_stop(hub.bus_stops.settings[stop_source],data)
            if data.get('auto_led') and stop_candidate['mode']=='bus_stop':raise ValueError('Crossing LEDs require crosswalk mode')
            if 'detection_mode' in data:
                mode=data['detection_mode']
                if mode not in ('full','crosswalk','tiles2','tiles4'):raise ValueError('Unknown detection mode')
                boundary=stop_candidate['boundary'] if stop_candidate['mode']=='bus_stop' else hub.profiles[stop_source].get('zone')
                if mode=='crosswalk' and not boundary:raise ValueError('Select the monitoring boundary first')
            if camera_settings:
                # Turning an automatic control off freezes its most recent camera setting.
                f=hub.frame or {}
                for key,held,field,default in (('auto_exposure','held_exposure','exposure_lines',3300),('auto_gain','held_gain','gain_code',228)):
                    if camera_settings.get(key) is False and hub.control.get(key,True) and held not in camera_settings:
                        value=f.get(field,hub.control.get(held,default))
                        camera_settings[held]=value if type(value) is int else hub.control.get(held,default)
                hub.control.update(camera_settings);atomic(ROOT/'control.json',hub.control)
            if 'detection_mode' in data:
                hub.control['detection_mode']=data['detection_mode']
                hub.control['crosswalk_detail']=data['detection_mode']=='crosswalk'
                atomic(ROOT/'control.json',hub.control)
            if 'brightness' in data:
                value=data['brightness']
                if type(value) is not int or not 0<=value<=100:raise ValueError('Brightness must be an integer from 0 to 100%')
                hub.brightness=value
                hub.save_led_settings()
            if any(key in data for key in LED_KEYS):
                hub.effects=effect_candidate;hub.save_led_settings()
            if 'auto_calibrate' in data:
                if data['auto_calibrate']:
                    if hub.control['source']!='camera':raise ValueError('Automatic calibration needs the live camera')
                    hub.control['marker_request']=uuid.uuid4().hex
                    hub.calibration_message='Looking for the printed ID 0 marker, flat on the ground and large enough to read.'
                else:
                    hub.control.pop('marker_request',None);hub.calibration_message='Marker search cancelled; saved calibration retained.'
                atomic(ROOT/'control.json',hub.control)
            if 'source' in data:hub.select_source(data['source'])
            if any(k in data for k in ('camera_mode','bus_stop_boundary','bus_stop_threshold')):hub.configure_stop(data)
            if 'model' in data:
                if data['model'] not in ('ncnn-320','ncnn-416','ncnn-640'):raise ValueError('Unknown model')
                hub.control['model']=data['model'];atomic(ROOT/'control.json',hub.control)
            if 'crosswalk_detail' in data:
                if type(data['crosswalk_detail']) is not bool:raise ValueError('Crosswalk detail must be true or false')
                if data['crosswalk_detail'] and not hub.profiles['camera'].get('zone'):raise ValueError('Select a crosswalk zone first')
                hub.control['crosswalk_detail']=data['crosswalk_detail'];atomic(ROOT/'control.json',hub.control)
                hub.control['detection_mode']='crosswalk' if data['crosswalk_detail'] else 'full';atomic(ROOT/'control.json',hub.control)
            if 'colour' in data:
                if data['colour'] not in ('natural','neutral'):raise ValueError('Unknown colour profile')
                hub.control['colour']=data['colour'];atomic(ROOT/'control.json',hub.control)
            if 'exposure' in data:
                if data['exposure'] not in ('motion','balanced','lowlight'):raise ValueError('Unknown exposure profile')
                hub.control['exposure']=data['exposure'];atomic(ROOT/'control.json',hub.control)
            if 'white_point' in data or data.get('rebalance'):
                hub.control['white_point']=list(points([data['white_point']],1)[0]) if data.get('white_point') else None
                hub.control['wb_revision']=time.time();atomic(ROOT/'control.json',hub.control)
            if any(k in data for k in ('line','zone','calibration')):hub.configure(data)
            if 'calibration' in data:
                hub.control.pop('marker_request',None);atomic(ROOT/'control.json',hub.control)
                hub.calibration_message='Measured ground calibration saved; reused after restart.' if data['calibration'] else 'Calibration removed. Use the printed marker or a measured ground rectangle to enable km/h.'
            if 'auto_led' in data:
                if data['auto_led'] and not hub.engine.zone:raise ValueError('Select a crosswalk zone first')
                hub.auto_led=data['auto_led'];hub.save_led_settings()
            if 'camera_rotation' in data:hub.rotate_camera(data['camera_rotation'])
            if data.get('reset_counts'):hub.engine.reset_counts()
            return web.json_response({'ok':True,'vision':hub.payload()['vision']})
        except (ValueError,TypeError,KeyError) as e:return web.json_response({'error':str(e)},status=400)
    async def upload(request):
        reader=await request.multipart();part=await reader.next()
        if part is None or not part.filename:return web.json_response({'error':'Choose a video file'},status=400)
        suffix=Path(part.filename).suffix.lower()
        if suffix not in ('.mp4','.mov','.avi','.mkv','.webm'):return web.json_response({'error':'Use MP4, MOV, AVI, MKV or WebM'},status=400)
        directory=ROOT/'uploads';directory.mkdir(exist_ok=True);path=directory/(uuid.uuid4().hex+suffix)
        size=0
        try:
            with path.open('wb') as f:
                while chunk:=await part.read_chunk():
                    size+=len(chunk)
                    if size>100*1024*1024:raise ValueError('Video exceeds 100 MB')
                    f.write(chunk)
            hub.select_source('replay',path)
            return web.json_response({'ok':True,'source':'replay'})
        except ValueError as e:
            path.unlink(missing_ok=True);return web.json_response({'error':str(e)},status=400)
    async def led_test(request):
        try:
            result=await hub.rpc('led_pin_test')
            if isinstance(result,(str,bytes)):result=json.loads(result)
            if not isinstance(result,dict):raise ValueError('Invalid LED diagnostic response')
            return web.json_response({'ok':True,'pin':result})
        except Exception as e:return web.json_response({'error':str(e)[:180]},status=503)
    recording_save_lock=asyncio.Lock()
    async def recording_state(request):
        return web.json_response({'clean':buffer_status(ROOT),'annotated':hub.recording.status(),'clips':list_clips(ROOT)})
    async def recording_command(request):
        try:
            data=await request.json();action=data.get('action')
            if action=='start':
                if not hub.fresh_live():raise ValueError('Wait for fresh live YOLO frames before recording')
                hub.recording.start()
            elif action=='stop':hub.recording.stop()
            elif action=='save_clean':
                if recording_save_lock.locked():raise ValueError('A clean clip is already being saved')
                async with recording_save_lock:
                    clip=await asyncio.to_thread(export_clean,ROOT)
                return web.json_response({'ok':True,'clip':clip})
            else:raise ValueError('Unknown recording action')
            return web.json_response({'ok':True,'annotated':hub.recording.status()})
        except (ValueError,TypeError,OSError) as error:
            return web.json_response({'error':str(error)[:180]},status=400)
    async def recording_download(request):
        try:path=download_path(ROOT,request.match_info['name'])
        except ValueError as error:return web.json_response({'error':str(error)},status=404)
        return web.FileResponse(path,headers={'Content-Disposition':'attachment; filename="'+path.name+'"'})
    async def recording_cleanup(app):await asyncio.to_thread(hub.recording.close)
    app.on_cleanup.append(recording_cleanup)
    app.router.add_get('/api/recordings',recording_state)
    app.router.add_post('/api/recordings',recording_command)
    app.router.add_get('/recordings/{name}',recording_download)
    app.router.add_post('/api/led-test',led_test)
    app.router.add_get('/',index);app.router.add_get('/dashboard.html',index)
    app.router.add_get('/ws',hub.websocket);app.router.add_get('/api/state',state)
    app.router.add_post('/api/config',configure);app.router.add_post('/api/video',upload)
    async def marker_file(request):return web.FileResponse(ROOT/'calibration-marker.svg',headers={'Content-Disposition':'inline; filename="calibration-marker.svg"'})
    app.router.add_get('/calibration-marker.svg',marker_file)
    return app

async def main():
    hub=Hub();app=make_app(hub);runner=web.AppRunner(app);await runner.setup()
    for port in (8090,8091,8765):await web.TCPSite(runner,'0.0.0.0',port).start()
    await asyncio.gather(hub.vision_loop(),hub.hardware_loop())

if __name__=='__main__':asyncio.run(main())
