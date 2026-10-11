import unittest
from camera_orientation import rotate_point,rotate_points,rotate_bounds,rotate_image,detail_crop,validate_rotation
from vision_engine import Calibration

class Tests(unittest.TestCase):
    def test_coordinate_inverse_and_calibration_scale(self):
        config={'points':[[.2,.2],[.8,.2],[.8,.8],[.2,.8]],'width':5,'length':10}
        before=Calibration(config)
        for rotation in (0,90,180,270):
            after=Calibration(dict(config,points=rotate_points(config['points'],rotation)))
            for point in ((.3,.4),(.65,.5)):
                world=after.project(rotate_point(point,rotation));expected=before.project(point)
                for a,b in zip(world,expected):self.assertAlmostEqual(a,b)
                for a,b in zip(rotate_point(rotate_point(point,rotation),-rotation),point):self.assertAlmostEqual(a,b)
    def test_native_tiles_match_rotated_full_view(self):
        import numpy as np
        raw=np.arange(80*120*3,dtype=np.uint8).reshape(80,120,3)
        class Camera:
            def detail_crop(self,bounds):
                a,b,c,d=bounds
                return raw[round(b*80):round(d*80),round(a*120):round(c*120)],bounds
        bounds=(.25,.25,.75,.75)
        for angle in (0,90,180,270):
            image=rotate_image(raw,angle);height,width=image.shape[:2]
            crop,actual=detail_crop(Camera(),bounds,angle)
            np.testing.assert_array_equal(crop,image[round(height*.25):round(height*.75),round(width*.25):round(width*.75)])
            np.testing.assert_allclose(actual,bounds)
        crop,_=detail_crop(Camera(),(.1,.2,.5,.6),180)
        np.testing.assert_array_equal(crop,rotate_image(raw,180)[16:48,12:60])
    def test_invalid_values(self):
        for value in (True,180.0,'180',45,-90,360,None):
            with self.assertRaises(ValueError):validate_rotation(value)
        for angle in (0,90,180,270):self.assertEqual(validate_rotation(angle),angle)

if __name__=='__main__':unittest.main()
