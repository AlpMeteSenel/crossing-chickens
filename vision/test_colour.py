import unittest
import numpy as np
from colour import render,CCM_RGB

class Tests(unittest.TestCase):
    def test_neutral_surfaces_remain_neutral(self):
        a=np.full((8,8),400,np.uint16)
        image=render(a,a,a,[1,1,1])
        self.assertLessEqual(int(image.max())-int(image.min()),1)
        self.assertTrue(np.allclose(CCM_RGB.sum(1),1,atol=1e-4))
    def test_black_and_clipping_and_colour_order(self):
        black=np.full((8,8),64,np.uint16);red=np.full((8,8),800,np.uint16)
        image=render(black,black,red,[1,1,1])
        self.assertGreater(int(image[0,0,2]),int(image[0,0,0]))
        self.assertTrue(np.all(render(black,black,black,[4,4,4])==0))
        self.assertEqual(image.dtype,np.uint8)
    def test_neutral_profile_is_reversible(self):
        b=np.full((8,8),100,np.uint16);g=np.full((8,8),200,np.uint16);r=np.full((8,8),300,np.uint16)
        self.assertFalse(np.array_equal(render(b,g,r,[1,1,1],True),render(b,g,r,[1,1,1],False)))
    def test_clipped_white_light_does_not_become_magenta(self):
        b=np.full((8,8),950,np.uint16);g=np.full((8,8),780,np.uint16);r=np.full((8,8),950,np.uint16)
        image=render(b,g,r,[2,1,1.5])
        self.assertLessEqual(int(image.max())-int(image.min()),1)

if __name__=='__main__':unittest.main()
