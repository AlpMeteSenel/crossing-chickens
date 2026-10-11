import unittest,math
from vision_engine import VisionEngine,Calibration

def frame(n,t,dets,kind='live',stream='one',motion_ts=None):
    f={'frame_id':n,'capture_ts':t,'stream_id':stream,'source_kind':kind,'src':kind,'w':1000,'h':1000,'dets':dets}
    if motion_ts is not None:f['motion_ts']=motion_ts
    return f
def det(cls,x,y,confidence=.9):return {'cls':cls,'conf':confidence,'box':[(x-.025)*1000,(y-.1)*1000,(x+.025)*1000,y*1000]}
CAL={'points':[[0,0],[1,0],[1,1],[0,1]],'width':10,'length':20}

class Tests(unittest.TestCase):
    def setUp(self):self.e=VisionEngine()
    def test_ids_count_once_recross_jitter(self):
        self.e.configure([[.5,.1],[.5,.9]],None,None)
        ids=[]
        for i,x in enumerate([.2,.3,.4,.49,.51,.6,.51,.49,.4,.3]):
            s=self.e.update(frame(i,100+i*.5,[det('car',x,.5)]),100+i*.5)
            ids.append(s['tracks'][0]['id'])
        self.assertEqual(len(set(ids)),1);self.assertEqual(s['counts'],{'car':1})
    def test_crossing_outside_line_endpoints_does_not_count(self):
        self.e.configure([[.5,.3],[.5,.6]],None,None)
        for i,x in enumerate([.4,.45,.55,.6]):s=self.e.update(frame(i,100+i*.5,[det('bicycle',x,.8)]),100+i*.5)
        self.assertEqual(s['counts'],{})
    def test_two_objects_get_unique_tracks(self):
        for i in range(4):s=self.e.update(frame(i,100+i*.25,[det('person',.2+i*.02,.4),det('person',.7-i*.02,.8)]),100+i*.25)
        self.assertEqual([t['id'] for t in s['tracks']],[1,2])
    def test_speed_and_confidence(self):
        self.e.configure([[.5,.1],[.5,.9]],None,CAL)
        for i in range(5):s=self.e.update(frame(i,100+i*.25,[det('car',.2+i*.05,.5,.87)]),100+i*.25)
        t=s['tracks'][0];self.assertAlmostEqual(t['speed_kmh'],7.2,places=1);self.assertEqual(t['conf'],.87)
        self.assertAlmostEqual(t['image_speed_px_s'],200,places=1)
    def test_person_speed(self):
        self.e.configure([[.1,.5],[.9,.5]],None,CAL)
        for i in range(5):s=self.e.update(frame(i,100+i*.25,[det('person',.3,.4+i*.015)]),100+i*.25)
        self.assertAlmostEqual(s['tracks'][0]['speed_kmh'],4.3,places=1)
    def test_replay_speed_uses_video_time(self):
        self.e.configure([[.1,.5],[.9,.5]],None,CAL)
        for i in range(5):s=self.e.update(frame(i,100+i*.4,[det('car',.2+i*.05,.5)],kind='replay',motion_ts=i*.25),100+i*.4)
        self.assertAlmostEqual(s['tracks'][0]['speed_kmh'],7.2,places=1)
    def test_no_speed_without_calibration(self):
        s=self.e.update(frame(1,100,[det('person',.3,.4)]),100)
        self.assertIsNone(s['tracks'][0]['speed_kmh'])
    def test_bad_calibration_rejected(self):
        for c in [dict(CAL,width=0),dict(CAL,length=float('nan')),dict(CAL,points=[[0,0],[1,1],[1,0],[0,1]])]:
            with self.assertRaises(ValueError):Calibration(c)
    def test_projective_calibration_maps_measured_corners(self):
        c=Calibration({'points':[[.3,.2],[.7,.2],[.9,.9],[.1,.9]],'width':6,'length':12})
        for p,expected in zip(c.polygon,[(0,0),(6,0),(6,12),(0,12)]):
            q=c.project(p)
            for a,b in zip(q,expected):self.assertAlmostEqual(a,b,places=6)
        self.assertIsNotNone(c.project((.01,.01)))
        self.assertIsNone(c.project((.5,-1/c.h[7])))
    def test_speed_outside_reference_rectangle(self):
        self.e.configure([[.5,.1],[.5,.9]],None,{'points':[[.4,.4],[.6,.4],[.6,.6],[.4,.6]],'width':2,'length':4})
        for i in range(5):s=self.e.update(frame(i,100+i*.25,[det('car',.15+i*.05,.8)]),100+i*.25)
        t=s['tracks'][0];self.assertAlmostEqual(t['speed_kmh'],7.2,places=1)
        self.assertEqual(t['speed_status'],'Extrapolated ground-plane estimate')
    def test_speed_at_sparse_detail_cadence(self):
        self.e.configure([[.5,.1],[.5,.9]],None,CAL)
        for i in range(4):s=self.e.update(frame(i,100+i*.9,[det('person',.2+i*.09,.5)]),100+i*.9)
        self.assertEqual(len(self.e.tracks),1);self.assertAlmostEqual(s['tracks'][0]['speed_kmh'],3.6,places=1)
    def test_recent_box_hold_does_not_invent_motion_samples(self):
        self.e.update(frame(1,100,[det('person',.3,.4)]),100)
        self.e.update(frame(2,100.3,[det('person',.3,.4)]),100.3)
        s=self.e.update(frame(3,100.6,[]),100.6)
        self.assertTrue(s['tracks'][0]['retained']);self.assertEqual(self.e.tracks[1].observations,2)
        self.assertFalse(s['tracks'][0]['inside'])
        s=self.e.update(frame(4,101.0,[]),101.0);self.assertEqual(s['tracks'],[])
    def test_zone_confirmation_hold_and_clear(self):
        self.e.configure([[.1,.6],[.9,.6]],[[.2,.2],[.8,.2],[.8,.8],[.2,.8]],None)
        s=self.e.update(frame(1,100,[det('person',.3,.4)]),100);self.assertFalse(s['occupied'])
        s=self.e.update(frame(2,100.25,[det('person',.3,.4)]),100.25);self.assertTrue(s['occupied'])
        s=self.e.update(frame(3,100.5,[]),100.5);self.assertTrue(s['occupied'])
        s=self.e.update(frame(4,101.2,[]),101.2);self.assertFalse(s['occupied'])
    def test_stale_still_and_bad_confidence(self):
        for f in [frame(1,90,[det('car',.3,.4)]),frame(2,100,[det('car',.3,.4)],kind='still'),frame(3,100,[det('car',.3,.4,8)])]:
            self.assertEqual(self.e.update(f,100)['tracks'],[])
    def test_duplicate_frame_not_counted_or_sampled_twice(self):
        f=frame(1,100,[det('person',.3,.4)])
        self.e.update(f,100);self.e.update(f,100.1)
        self.assertEqual(self.e.tracks[1].observations,1)

if __name__=='__main__':unittest.main()
