import unittest
import cv2
import numpy as np
from marker_calibration import MarkerCalibration, SIDE_METRES

def scene(size=160, x=180):
    image=np.full((480,640,3),255,np.uint8)
    marker=cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11),0,size)
    image[140:140+size,x:x+size]=cv2.cvtColor(marker,cv2.COLOR_GRAY2BGR)
    return image

class Tests(unittest.TestCase):
    def test_three_stable_observations_produce_measured_reference(self):
        detector=MarkerCalibration();image=scene()
        self.assertIsNone(detector.find(image));self.assertIsNone(detector.find(image))
        calibration=detector.find(image)
        self.assertEqual(calibration['width'],SIDE_METRES)
        self.assertEqual(calibration['length'],SIDE_METRES)
        expected=np.array([[180,140],[339,140],[339,299],[180,299]])/np.array([640,480])
        np.testing.assert_allclose(calibration['points'],expected,atol=.003)

    def test_moving_marker_restarts_stability_check(self):
        detector=MarkerCalibration();detector.find(scene());detector.find(scene())
        self.assertIsNone(detector.find(scene(x=220)))
        self.assertEqual(len(detector.samples),1)

    def test_missing_and_tiny_markers_cannot_replace_calibration(self):
        detector=MarkerCalibration()
        self.assertIsNone(detector.find(np.full((480,640,3),255,np.uint8)))
        self.assertIsNone(detector.find(scene(size=24)))
        self.assertEqual(len(detector.samples),0)

if __name__=='__main__':unittest.main()
