import unittest
from auto_camera import auto_step,validate_controls,gain_factor

class Tests(unittest.TestCase):
    def test_disabled_controls_hold(self):
        self.assertEqual(auto_step(1200,100,12,3300,False,False),(1200,100))
    def test_exposure_only_preserves_gain_and_respects_blur_limit(self):
        shutter,gain=auto_step(1100,100,12,1100,True,False)
        self.assertEqual((shutter,gain),(1100,100))
        self.assertLess(auto_step(1100,100,800,1100,True,False)[0],1100)
    def test_gain_only_preserves_shutter_and_is_bounded(self):
        shutter,gain=auto_step(1200,100,12,3300,False,True)
        self.assertEqual(shutter,1200);self.assertGreater(gain,100)
        self.assertEqual(auto_step(3300,232,1,3300,False,True),(3300,232))
    def test_both_prefer_shutter_before_gain(self):
        shutter,gain=auto_step(1000,128,175,3300)
        self.assertGreater(shutter,1000);self.assertEqual(gain,0)
        shutter,gain=auto_step(3300,100,100,3300)
        self.assertEqual(shutter,3300);self.assertGreater(gain,100)
    def test_deadband_and_invalid_metering_hold(self):
        for level in (350,float('nan')):self.assertEqual(auto_step(1000,100,level,3300),(1000,100))
        self.assertAlmostEqual(gain_factor(232),10.6666666667)
    def test_malformed_controls_rejected(self):
        for data in ({'auto_gain':1},{'held_gain':233},{'held_exposure':99},{'held_exposure':6001},{'auto_exposure':'yes'}):
            with self.assertRaises(ValueError):validate_controls(data)

if __name__=='__main__':unittest.main()
