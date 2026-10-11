import time,unittest,numpy as np
from process_capture import ProcessCamera

class FakeCamera:
    def __init__(self):
        self.sequence=0;self.gains=np.ones(3);self.natural_colour=True;self.exposure=3300;self.gain=228
        self.exposure_ms=32.2;self.colour_warning=None
    @property
    def gain_x(self):return 256/(256-self.gain)
    def set_exposure_profile(self,profile):pass
    def set_auto_controls(self,ae,ag,exposure,gain):
        if not ae:self.exposure=exposure
        if not ag:self.gain=gain
    def rebalance(self):pass
    def set_white_reference(self,point):pass
    def read(self):
        time.sleep(.02);self.sequence+=1;self.timestamp=time.monotonic()
        self.raw=np.full((20,20),self.sequence,np.uint16)
        return True,np.full((10,10,3),self.sequence,np.uint8)
    def release(self):pass

class FailedCamera(FakeCamera):
    def read(self):return False,None

class Tests(unittest.TestCase):
    def test_latest_frame_and_raw_remain_coherent_for_slow_consumer(self):
        camera=ProcessCamera(FakeCamera,(10,10,3),(20,20))
        try:
            ok,first=camera.read();self.assertTrue(ok)
            time.sleep(.12);ok,second=camera.read();self.assertTrue(ok)
            self.assertGreater(int(second[0,0,0]),int(first[0,0,0])+2)
            self.assertEqual(int(second[0,0,0]),int(camera.selected_raw[0,0]))
            timestamp=camera.timestamp;time.sleep(.05)
            self.assertEqual(camera.timestamp,timestamp);self.assertEqual(int(second[0,0,0]),int(camera.selected_raw[0,0]))
        finally:camera.release()
        self.assertFalse(camera.process.is_alive())
    def test_controls_reach_capture_process_and_metadata(self):
        camera=ProcessCamera(FakeCamera,(10,10,3),(20,20))
        try:
            self.assertTrue(camera.read()[0]);camera.set_auto_controls(False,False,1100,100)
            deadline=time.monotonic()+2
            while time.monotonic()<deadline:
                self.assertTrue(camera.read()[0])
                if camera.gain==100 and camera.exposure==1100:break
            self.assertEqual(camera.gain,100);self.assertEqual(camera.exposure,1100)
        finally:camera.release()
    def test_failed_capture_stops_child(self):
        camera=ProcessCamera(FailedCamera,(10,10,3),(20,20))
        self.assertFalse(camera.read()[0]);camera.release();self.assertFalse(camera.process.is_alive())

if __name__=='__main__':unittest.main()
