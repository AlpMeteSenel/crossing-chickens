import tempfile,unittest
from pathlib import Path
from bus_stop import BusStops

BOUNDARY=[[.2,.2],[.8,.2],[.8,.8],[.2,.8]]
def person(i=1,x=.5,y=.5,**kwargs):
    return dict({'id':i,'cls':'person','confirmed':True,'box':[x-.03,y-.15,x+.03,y],'conf':.9},**kwargs)
def frame(i,ts,kind='live'):return {'frame_id':i,'stream_id':'test','capture_ts':ts,'w':1000,'h':1000,'source_kind':kind}

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.stops=BusStops(self.root)
        self.stops.configure('camera',{'camera_mode':'bus_stop','bus_stop_boundary':BOUNDARY,'bus_stop_threshold':2})
    def tearDown(self):self.tmp.cleanup()
    def update(self,i,ts,tracks,kind='live'):
        f=frame(i,ts,kind);self.stops.update('camera',tracks,f,ts);return self.stops.snapshot('camera',f,ts)
    def test_only_confirmed_current_in_zone_people_count_once(self):
        tracks=[person(1),person(1),person(2,x=.95),person(3,confirmed=False),person(4,retained=True),person(5,cls='car')]
        state=self.update(1,100,tracks)
        self.assertEqual(state['count'],1);self.assertEqual(state['occupancy_percent'],50)
        self.assertEqual(state['inside_ids'],[1]);self.assertFalse(state['threshold_reached'])
    def test_two_unique_frames_trigger_one_durable_warning_then_rearm(self):
        people=[person(1),person(2)]
        self.assertFalse(self.update(1,100,people)['threshold_reached'])
        self.assertFalse(self.update(1,100,people)['threshold_reached'])
        state=self.update(2,100.2,people);self.assertTrue(state['threshold_reached'])
        self.assertEqual(len(self.stops.history),1);self.update(3,100.4,people)
        self.assertEqual(len(self.stops.history),1)
        self.update(4,100.6,[]);self.update(5,102.7,[])
        self.update(6,102.8,people);self.update(7,103,people)
        self.assertEqual(len(self.stops.history),2)
        self.assertEqual(len((self.root/'bus_stop_warnings.jsonl').read_text().splitlines()),2)
    def test_settings_history_and_active_episode_survive_restart(self):
        people=[person(1),person(2)];self.update(1,100,people);self.update(2,100.2,people)
        restored=BusStops(self.root)
        self.assertEqual(restored.settings['camera']['threshold'],2)
        self.assertEqual(restored.settings['camera']['boundary'],BOUNDARY)
        self.assertEqual(len(restored.history),1)
        restored.update('camera',people,frame(3,101),101)
        self.assertEqual(len(restored.history),1)
    def test_stale_pause_does_not_show_zero_or_duplicate_active_warning(self):
        people=[person(1),person(2)];self.update(1,100,people);self.update(2,100.2,people)
        self.stops.update('camera',people,frame(3,100.3),103)
        self.assertIsNone(self.stops.snapshot('camera',frame(3,100.3),103)['count'])
        self.update(4,103.1,people);self.update(5,103.3,people)
        self.assertEqual(len(self.stops.history),1)
    def test_preview_sources_never_save_live_warnings_or_poison_live_episode(self):
        people=[person(1),person(2)]
        self.update(1,100,people,'simulation');self.update(2,100.2,people,'simulation')
        self.assertEqual(len(self.stops.history),0);self.assertFalse(self.stops.runtime['camera']['active'])
        self.stops.configure('simulation',{'camera_mode':'bus_stop','bus_stop_boundary':BOUNDARY,'bus_stop_threshold':2})
        for i in (1,2):self.stops.update('simulation',people,frame(i,100+i*.1,'simulation'),100+i*.1)
        state=self.stops.snapshot('simulation',frame(2,100.2,'simulation'),100.2)
        self.assertTrue(state['threshold_reached']);self.assertTrue(state['preview'])
        self.assertFalse((self.root/'bus_stop_warnings.jsonl').exists())
    def test_invalid_settings_cannot_change_saved_stop(self):
        original=dict(self.stops.settings['camera'])
        for data in ({'bus_stop_threshold':0},{'bus_stop_threshold':True},{'bus_stop_threshold':2.5},
                     {'camera_mode':'bad'},{'bus_stop_boundary':[[0,0],[1,1],[1,0],[0,1]]}):
            with self.assertRaises(ValueError):self.stops.configure('camera',data)
            self.assertEqual(self.stops.settings['camera'],original)

if __name__=='__main__':unittest.main()
