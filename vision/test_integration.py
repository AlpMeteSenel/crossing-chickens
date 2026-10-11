"""Real HTTP/WebSocket handlers and fake hardware; no physical LEDs are actuated."""
import asyncio,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from aiohttp.test_utils import TestClient,TestServer
import collector_integrated as module
from test_vision import frame,det

class FakeBridge:
    def __init__(self):self.calls=[];self.mode=10;self.brightness=10;self.effects=None
    def call(self,name,*args,timeout=None):
        self.calls.append((name,args))
        if name=='read_sensors':return json.dumps({'light':632,'temp_c':22.5,'hum_pct':45,'pir':False,'gx':0,'gy':0,'gz':0,'led_mode':self.mode})
        if name=='set_mode':self.mode=args[0];return True
        if name=='set_led':self.mode=10;return True
        if name=='set_effect_config':self.effects=args;return True
        if name=='led_pin_test':return json.dumps({'high':1,'low':0,'high_error':0,'low_error':0,'configuration_ok':True})
        if name=='led_status':return json.dumps({'driver_error':0,'configuration_ok':True})
        if name=='set_brightness':self.brightness=args[0];return True
        return False

class Tests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.patch=patch.object(module,'ROOT',Path(self.tmp.name));self.patch.start()
        (module.ROOT/'dashboard.html').write_text('<h1>dashboard</h1>')
        self.bridge=FakeBridge();self.hub=module.Hub(lambda:self.bridge)
        self.client=TestClient(TestServer(module.make_app(self.hub)));await self.client.start_server()
    async def asyncTearDown(self):
        await self.client.close();self.hub.pool.shutdown(wait=True);self.patch.stop();self.tmp.cleanup()
    async def test_recording_routes_validate_and_local_downloads(self):
        response=await self.client.get('/api/recordings');self.assertEqual(response.status,200)
        state=await response.json();self.assertEqual(state['clean']['window_seconds'],15)
        response=await self.client.post('/api/recordings',json={'action':'start'});self.assertEqual(response.status,400)
        response=await self.client.post('/api/recordings',json={'action':'save_clean'});self.assertEqual(response.status,400)
        response=await self.client.post('/api/recordings',json={'action':'unknown'});self.assertEqual(response.status,400)
        response=await self.client.get('/recordings/control.json');self.assertEqual(response.status,404)
        response=await self.client.post('/api/recordings',json={'action':'stop'});self.assertEqual(response.status,200)
    async def test_live_recording_start_and_stop_are_independent_of_leds(self):
        self.hub.frame=frame(1,time.time(),[])
        self.hub.auto_led=True
        response=await self.client.post('/api/recordings',json={'action':'start'});self.assertEqual(response.status,200)
        self.assertTrue(self.hub.recording.status()['active']);self.assertTrue(self.hub.auto_led)
        response=await self.client.post('/api/recordings',json={'action':'stop'});self.assertEqual(response.status,200)
        self.assertTrue(self.hub.auto_led)
        await asyncio.to_thread(self.hub.recording.close)

    async def test_led_pin_diagnostic_uses_serialized_rpc(self):
        r=await self.client.post('/api/led-test')
        self.assertEqual(r.status,200)
        data=await r.json();self.assertTrue(data['ok'])
        self.assertEqual((data['pin']['high'],data['pin']['low']),(1,0))
        self.assertIn(('led_pin_test',()),self.bridge.calls)
    async def test_crossing_automation_survives_restart_but_manual_override_persists_off(self):
        zone=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]
        r=await self.client.post('/api/config',json={'zone':zone,'auto_led':True})
        self.assertEqual(r.status,200)
        saved=module.Hub(lambda:self.bridge)
        try:
            self.assertTrue(saved.auto_led)
            self.assertEqual(saved.desired_auto(),('set_led',(0,0,0)))
        finally:saved.pool.shutdown(wait=True)
        self.hub.manual_command(('set_mode',(22,)))
        saved=module.Hub(lambda:self.bridge)
        try:self.assertFalse(saved.auto_led)
        finally:saved.pool.shutdown(wait=True)
    async def test_bus_stop_and_missing_zone_do_not_resume_crossing_automation(self):
        await self.client.post('/api/config',json={'zone':[[.2,.2],[.8,.2],[.8,.8],[.2,.8]],'auto_led':True})
        await self.client.post('/api/config',json={'camera_mode':'bus_stop'})
        saved=module.Hub(lambda:self.bridge)
        try:self.assertFalse(saved.auto_led)
        finally:saved.pool.shutdown(wait=True)
        r=await self.client.post('/api/config',json={'auto_led':'true'})
        self.assertEqual(r.status,400)
    async def test_effect_settings_save_apply_and_brightness_preserves_them(self):
        r=await self.client.post('/api/config',json={'led_theme':'sunset','led_speed':150,'led_wave_width':9})
        self.assertEqual(r.status,200)
        r=await self.client.post('/api/config',json={'brightness':36});self.assertEqual(r.status,200)
        restored=module.Hub(lambda:self.bridge)
        try:
            self.assertEqual(restored.effects,self.hub.effects)
            self.assertEqual(restored.brightness,36)
        finally:restored.pool.shutdown(wait=True)
        task=asyncio.create_task(self.hub.hardware_loop())
        try:
            await asyncio.sleep(.15)
            self.assertEqual(self.bridge.effects,(0xff7a18,0xe52e71,150,9))
        finally:task.cancel();await asyncio.gather(task,return_exceptions=True)
    async def test_invalid_effect_settings_reject_before_mutation(self):
        before=dict(self.hub.effects)
        for data in ({'led_speed':0},{'led_speed':True},{'led_wave_width':16},{'led_wave_width':0},
                     {'led_theme':'missing'},{'led_primary':'red'},{'led_secondary':'#12345'},
                     {'led_theme':'neon','brightness':101}):
            r=await self.client.post('/api/config',json=data);self.assertEqual(r.status,400)
            self.assertEqual(self.hub.effects,before)
            self.assertEqual(self.hub.brightness,10)
    async def test_custom_colours_override_theme(self):
        r=await self.client.post('/api/config',json={'led_primary':'#Ff0000','led_secondary':'#0000Ff'})
        self.assertEqual(r.status,200);self.assertEqual(self.hub.effects['theme'],'custom')
        self.assertEqual(self.hub.effects['primary'],'#ff0000')
        ws=await self.client.ws_connect('/ws')
        for mode in range(22,34):
            await ws.send_json({'mode':mode});await asyncio.sleep(.01)
            self.assertEqual(self.hub.manual,('set_mode',(mode,)))
        await ws.close()
    async def test_rotation_preserves_geometry_scale_counts_and_restart(self):
        zone=[[.1,.2],[.7,.2],[.7,.8],[.1,.8]]
        calibration={'points':zone,'width':5,'length':8}
        await self.client.post('/api/config',json={'zone':zone,'calibration':calibration,'auto_led':True})
        self.hub.engine.counts['person']=7
        self.hub.control['white_point']=[.25,.3]
        await self.client.post('/api/config',json={'bus_stop_boundary':zone})
        old=json.loads(json.dumps(self.hub.profiles['camera']))
        result=await self.client.post('/api/config',json={'camera_rotation':180})
        self.assertEqual(result.status,200)
        self.assertEqual(self.hub.payload()['vision']['camera_rotation'],180)
        self.assertEqual(self.hub.engine.counts['person'],7)
        self.assertTrue(self.hub.auto_led)
        self.assertIsNone(self.hub.frame)
        for original,rotated in zip(old['zone'],self.hub.profiles['camera']['zone']):
            for a,b in zip(original,rotated):self.assertAlmostEqual(b,1-a)
        self.assertEqual(self.hub.profiles['camera']['calibration']['width'],5)
        self.assertEqual(self.hub.bus_stops.settings['camera']['boundary'],self.hub.profiles['camera']['zone'])
        restarted=module.Hub(lambda:self.bridge)
        try:
            self.assertEqual(restarted.control['camera_rotation'],180)
            self.assertEqual(restarted.profiles['camera'],self.hub.profiles['camera'])
        finally:restarted.pool.shutdown(wait=True)
        await self.client.post('/api/config',json={'camera_rotation':0})
        for field in ('line','zone'):
            for original,restored in zip(old[field],self.hub.profiles['camera'][field]):
                for a,b in zip(original,restored):self.assertAlmostEqual(a,b)
    async def test_rotation_rejects_invalid_without_changes(self):
        old=dict(self.hub.control)
        for value in (True,'180',180.0,45,-90):
            result=await self.client.post('/api/config',json={'camera_rotation':value,'brightness':80})
            self.assertEqual(result.status,400)
            self.assertEqual(self.hub.control,old)
            self.assertEqual(self.hub.brightness,10)

    async def test_config_validates_before_changing_geometry(self):
        r=await self.client.post('/api/config',json={'auto_led':True});self.assertEqual(r.status,400)
        r=await self.client.post('/api/config',json={'zone':[[.2,.2],[.8,.2],[.8,.8],[.2,.8]],'auto_led':True});self.assertEqual(r.status,200)
        old=self.hub.engine.zone
        r=await self.client.post('/api/config',json={'zone':[[0,0],[1,1],[1,0],[0,1]]});self.assertEqual(r.status,400);self.assertEqual(self.hub.engine.zone,old)
    async def test_manual_off_uses_rgb_not_hub5_mode6(self):
        ws=await self.client.ws_connect('/ws');self.hub.auto_led=True
        await ws.send_json({'mode':6});await asyncio.sleep(.02)
        self.assertFalse(self.hub.auto_led);self.assertEqual(self.hub.manual,('set_led',(0,0,0)))
        await ws.close()
    async def test_new_animations_roundtrip_and_preserve_brightness(self):
        self.hub.brightness=18
        task=asyncio.create_task(self.hub.hardware_loop())
        ws=await self.client.ws_connect('/ws')
        try:
            for mode in range(15,22):
                self.hub.auto_led=True
                await ws.send_json({'mode':mode})
                for _ in range(25):
                    await asyncio.sleep(.02)
                    if self.bridge.mode==mode and self.hub.applied_revision==self.hub.manual_revision:break
                self.assertEqual(self.bridge.mode,mode)
                self.assertFalse(self.hub.auto_led)
                self.assertEqual(self.bridge.brightness,18)
                self.assertIn(('set_mode',(mode,)),self.bridge.calls)
        finally:
            await ws.close();task.cancel();await asyncio.gather(task,return_exceptions=True)
    async def test_animation_rejects_invalid_mode_without_changing_command(self):
        ws=await self.client.ws_connect('/ws')
        try:
            for mode in (-1,34,True,15.5,'15',None):
                await ws.send_json({'mode':mode})
                response=await ws.receive_json(timeout=1)
                self.assertIn('error',response)
                self.assertIsNone(self.hub.manual)
                self.assertEqual(self.hub.manual_revision,0)
        finally:await ws.close()
    async def test_live_crossing_triggers_then_stale_turns_off(self):
        self.hub.configure({'zone':[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]});self.hub.auto_led=True
        now=time.time()
        self.hub.engine.update(frame(1,now-.25,[det('person',.3,.4)]),now-.25)
        self.hub.frame=frame(2,now,[det('person',.3,.4)])
        self.hub.engine.update(self.hub.frame,now)
        self.assertEqual(self.hub.desired_auto(),('set_mode',(11,)))
        task=asyncio.create_task(self.hub.hardware_loop())
        try:
            await asyncio.sleep(.15)
            self.assertIn(('set_mode',(11,)),self.bridge.calls)
            self.hub.frame['capture_ts']=time.time()-3
            await asyncio.sleep(.15)
            self.assertIn(('set_led',(0,0,0)),self.bridge.calls)
        finally:task.cancel();await asyncio.gather(task,return_exceptions=True)
    async def test_simulation_and_replay_never_trigger_leds(self):
        for kind in ('simulation','replay','still'):
            self.hub.frame=frame(1,time.time(),[det('person',.3,.4)],kind=kind)
            self.hub.engine.snapshot['occupied']=True;self.hub.auto_led=True
            self.assertEqual(self.hub.desired_auto(),('set_led',(0,0,0)))
    async def test_source_switch_cannot_use_previous_live_frame(self):
        self.hub.frame=frame(1,time.time(),[det('person',.3,.4)])
        self.hub.select_source('simulation');self.assertFalse(self.hub.fresh_live())
        self.assertFalse(self.hub.auto_led)
    async def test_sensor_and_state_endpoint(self):
        sensors=await self.hub.rpc('read_sensors');self.assertEqual(json.loads(sensors)['temp_c'],22.5)
        r=await self.client.get('/api/state');self.assertEqual(r.status,200)
        data=await r.json();self.assertIn('vision',data)
    async def test_bus_stop_mode_boundary_threshold_persist(self):
        boundary=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]];self.hub.auto_led=True
        r=await self.client.post('/api/config',json={'camera_mode':'bus_stop','bus_stop_boundary':boundary,'bus_stop_threshold':3})
        self.assertEqual(r.status,200);self.assertFalse(self.hub.auto_led)
        data=await r.json();self.assertEqual(data['vision']['camera_mode'],'bus_stop')
        restored=module.Hub(lambda:self.bridge)
        try:
            self.assertEqual(restored.control['camera_mode'],'bus_stop')
            self.assertEqual(restored.control['bus_stop_boundary'],boundary)
            self.assertEqual(restored.payload()['vision']['bus_stop']['threshold'],3)
        finally:restored.pool.shutdown(wait=True)
        r=await self.client.post('/api/config',json={'auto_led':True});self.assertEqual(r.status,400)
    async def test_invalid_stop_config_does_not_change_camera_or_stop(self):
        old=dict(self.hub.control);stop=dict(self.hub.bus_stops.settings['camera'])
        for data in ({'camera_mode':'bus_stop','bus_stop_threshold':0},{'bus_stop_threshold':True},
                     {'bus_stop_boundary':[[0,0],[1,1],[1,0],[0,1]]}):
            r=await self.client.post('/api/config',json=data);self.assertEqual(r.status,400)
            self.assertEqual(self.hub.control,old);self.assertEqual(self.hub.bus_stops.settings['camera'],stop)
    async def test_actual_vision_loop_saves_threshold_warning_once(self):
        boundary=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]
        r=await self.client.post('/api/config',json={'camera_mode':'bus_stop','bus_stop_boundary':boundary,'bus_stop_threshold':1})
        self.assertEqual(r.status,200);task=asyncio.create_task(self.hub.vision_loop())
        try:
            for i in (1,2,3,4):
                now=time.time();module.atomic(module.ROOT/'vision.json',frame(i,now,[det('person',.3,.4)]))
                await asyncio.sleep(.13)
            r=await self.client.get('/api/state');state=(await r.json())['vision']['bus_stop']
            self.assertEqual(state['count'],1);self.assertTrue(state['threshold_reached'])
            self.assertEqual(len(state['warnings']),1)
            self.assertEqual(state['warnings'][0]['severity'],'warning')
            self.assertTrue((module.ROOT/'bus_stop_warnings.jsonl').exists())
        finally:task.cancel();await asyncio.gather(task,return_exceptions=True)
    async def test_brightness_persists_and_preserves_automation(self):
        self.hub.auto_led=True
        r=await self.client.post('/api/config',json={'brightness':27});self.assertEqual(r.status,200)
        self.assertTrue(self.hub.auto_led)
        restored=module.Hub(lambda:self.bridge)
        try:self.assertEqual(restored.brightness,27)
        finally:restored.pool.shutdown(wait=True)
        task=asyncio.create_task(self.hub.hardware_loop())
        try:
            await asyncio.sleep(.1)
            self.assertIn(('set_brightness',(27,)),self.bridge.calls)
            self.assertEqual(self.hub.payload()['led']['applied_percent'],27)
        finally:task.cancel();await asyncio.gather(task,return_exceptions=True)
    async def test_brightness_rejects_out_of_range_and_nonintegers(self):
        for value in (-1,101,True,12.5,'50'):
            r=await self.client.post('/api/config',json={'brightness':value});self.assertEqual(r.status,400)
            self.assertEqual(self.hub.brightness,10)
    async def test_saved_camera_calibration_and_preferences_reused(self):
        from test_vision import CAL
        self.hub.configure({'calibration':CAL,'zone':[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]})
        r=await self.client.post('/api/config',json={'model':'ncnn-416','crosswalk_detail':True});self.assertEqual(r.status,200)
        restored=module.Hub(lambda:self.bridge)
        try:
            self.assertEqual(restored.profiles['camera']['calibration'],CAL)
            self.assertEqual(restored.control['model'],'ncnn-416');self.assertTrue(restored.control['crosswalk_detail'])
        finally:restored.pool.shutdown(wait=True)
    async def test_independent_auto_controls_hold_and_persist_latest_settings(self):
        self.hub.frame={'exposure_lines':1800,'gain_code':150}
        r=await self.client.post('/api/config',json={'auto_exposure':False,'auto_gain':False,'detection_mode':'tiles2'})
        self.assertEqual(r.status,200);self.assertEqual(self.hub.control['held_exposure'],1800)
        self.assertEqual(self.hub.control['held_gain'],150)
        restored=module.Hub(bridge_factory=lambda:FakeBridge())
        try:
            self.assertFalse(restored.control['auto_exposure']);self.assertFalse(restored.control['auto_gain'])
            self.assertEqual(restored.control['held_gain'],150);self.assertEqual(restored.control['detection_mode'],'tiles2')
        finally:restored.pool.shutdown(wait=False)
    async def test_invalid_camera_controls_are_rejected_before_mutation(self):
        old=dict(self.hub.control)
        for data in ({'auto_gain':1},{'auto_exposure':False,'detection_mode':'unknown'},{'held_gain':300}):
            r=await self.client.post('/api/config',json=data);self.assertEqual(r.status,400)
            self.assertEqual(self.hub.control,old)
    async def test_marker_start_cancel_preserves_saved_calibration(self):
        from test_vision import CAL
        self.hub.configure({'calibration':CAL})
        r=await self.client.post('/api/config',json={'auto_calibrate':True});self.assertEqual(r.status,200)
        self.assertTrue(self.hub.control.get('marker_request'))
        self.assertEqual(self.hub.profiles['camera']['calibration'],CAL)
        r=await self.client.post('/api/config',json={'auto_calibrate':False});self.assertEqual(r.status,200)
        self.assertNotIn('marker_request',self.hub.control)
        self.assertEqual(self.hub.profiles['camera']['calibration'],CAL)
    async def test_manual_calibration_cancels_pending_marker_search(self):
        from test_vision import CAL
        await self.client.post('/api/config',json={'auto_calibrate':True})
        r=await self.client.post('/api/config',json={'calibration':CAL});self.assertEqual(r.status,200)
        self.assertNotIn('marker_request',self.hub.control)
        self.assertEqual(self.hub.profiles['camera']['calibration'],CAL)

if __name__=='__main__':unittest.main()
