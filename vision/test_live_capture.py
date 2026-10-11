import time,unittest
import numpy as np
from live_capture import LiveCamera

class FakeCamera:
    def __init__(self):
        self.i=0;self.gains=np.ones(3);self.natural_colour=True;self.exposure=3300;self.exposure_ms=60
        self.colour_warning=None;self.closed=False
        self.gain=228;self.gain_x=9.14
    def set_exposure_profile(self,p):pass
    def set_auto_controls(self,*args):pass
    def set_white_reference(self,p):pass
    def rebalance(self):pass
    def read(self):
        time.sleep(.01);self.i+=1;self.timestamp=time.monotonic()
        self.raw=np.full((20,20),self.i,np.uint16)
        return True,np.full((10,10,3),self.i,np.uint8)
    def detail_crop(self,bounds,raw,gains,natural):return raw,bounds
    def release(self):self.closed=True

class Tests(unittest.TestCase):
    def test_slow_consumer_gets_latest_coherent_frame_and_crop(self):
        camera=LiveCamera(FakeCamera)
        try:
            ok,first=camera.read();self.assertTrue(ok)
            time.sleep(.07)
            ok,new=camera.read();self.assertTrue(ok);self.assertGreater(int(new[0,0,0]),int(first[0,0,0])+2)
            selected=int(new[0,0,0]);timestamp=camera.timestamp
            time.sleep(.03)
            crop,_=camera.detail_crop((0,0,1,1));self.assertEqual(int(crop[0,0]),selected)
            self.assertEqual(camera.timestamp,timestamp)
            self.assertLess(time.monotonic()-timestamp,.08)
        finally:camera.release()
        self.assertTrue(camera.reader.closed);self.assertFalse(camera.thread.is_alive())
    def test_read_failure_releases_device(self):
        class Failed(FakeCamera):
            def read(self):return False,None
        camera=LiveCamera(Failed)
        self.assertFalse(camera.read()[0]);camera.release()
        self.assertTrue(camera.reader.closed)

if __name__=='__main__':unittest.main()
