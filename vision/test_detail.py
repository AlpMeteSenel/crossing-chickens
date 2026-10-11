import unittest
import cv2,numpy as np
from marker_calibration import MarkerCalibration,marker_svg
from vision_detail import focus_bounds,tile_bounds,sweep_bounds,map_crop,merge_detections
from camera import CSICamera

class Tests(unittest.TestCase):
    def test_sweep_bounds_work_and_covers_all_tiles_without_stale_reuse(self):
        for count in (2,4):
            self.assertEqual([sweep_bounds(count,i)[0] for i in range(count)],tile_bounds(count))
            self.assertEqual(sweep_bounds(count,count),sweep_bounds(count,0))
    def test_overlap_seam_objects_map_and_deduplicate_for_all_classes(self):
        bounds=tile_bounds(2);self.assertAlmostEqual(bounds[0][2]-bounds[1][0],.2)
        right=map_crop([{'cls':'car','conf':.7,'box':[10,50,110,250]}],bounds[1],(600,600,3),(600,1000,3),classes=None)
        # Matching seam boxes map to [410,50,510,250] in global coordinates.
        left=map_crop([{'cls':'car','conf':.8,'box':[410,50,510,250]}],bounds[0],(600,600,3),(600,1000,3),classes=None)
        self.assertEqual(len(merge_detections(left+right)),1)
        self.assertEqual(len(tile_bounds(4)),4)
        self.assertEqual(map_crop([{'cls':'car','conf':.8,'box':[0,50,50,250]}],bounds[1],(600,600,3),(600,1000,3),classes=None),[])
    def test_native_bayer_crop_preserves_red_blue_and_geometry(self):
        camera=object.__new__(CSICamera);camera.gains=np.ones(3);camera.natural_colour=False
        camera.raw=np.zeros((100,120),np.uint16)
        camera.raw[::2,::2]=800;camera.raw[1::2,1::2]=100
        camera.raw[::2,1::2]=camera.raw[1::2,::2]=400
        image,bounds=camera.detail_crop((.25,.2,.75,.8))
        self.assertEqual(image.shape,(60,60,3));self.assertGreater(int(image[20,20,2]),int(image[20,20,0]))
        self.assertEqual(bounds,(.25,.2,.75,.8))
    def test_crop_maps_back_to_full_frame_and_keeps_complete_people(self):
        d={'cls':'person','conf':.3,'box':[100,20,200,250]}
        result=map_crop([d],(.5,.2,1,.8),(600,500,3),(1000,1000,3))
        np.testing.assert_allclose(result[0]['box'],[600,220,700,450]);self.assertTrue(result[0]['detail'])
        self.assertEqual(map_crop([dict(d,box=[100,0,200,600])],(.5,.2,1,.8),(600,500,3),(1000,1000,3)),[])
    def test_duplicate_person_removed_without_merging_adjacent_people(self):
        ds=[{'cls':'person','conf':.5,'box':[10,10,30,50]}, {'cls':'person','conf':.9,'box':[11,11,31,51]},
            {'cls':'person','conf':.8,'box':[40,10,60,50]}, {'cls':'car','conf':.7,'box':[10,10,30,50]}]
        self.assertEqual(len(merge_detections(ds)),3)
    def test_focus_includes_body_above_ground_zone(self):
        bounds=focus_bounds([[.7,.5],[.9,.5],[.9,.6],[.7,.6]])
        self.assertLess(bounds[1],.3);self.assertEqual(focus_bounds(None),None)
    def test_printed_marker_detected_only_after_three_stable_frames(self):
        dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
        marker=cv2.aruco.generateImageMarker(dictionary,0,240)
        image=np.full((400,500,3),255,np.uint8);image[80:320,130:370]=marker[:,:,None]
        detector=MarkerCalibration()
        self.assertIsNone(detector.find(image));self.assertIsNone(detector.find(image))
        c=detector.find(image);self.assertEqual(c['width'],.16)
        self.assertEqual(len(c['points']),4)
        self.assertIn('160 mm',marker_svg())
    def test_tiny_marker_rejected(self):
        marker=cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11),0,24)
        image=np.full((400,500,3),255,np.uint8);image[100:124,100:124]=marker[:,:,None]
        detector=MarkerCalibration()
        for _ in range(4):self.assertIsNone(detector.find(image))

if __name__=='__main__':unittest.main()
