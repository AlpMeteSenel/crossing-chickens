import unittest,numpy as np
from unpack10 import unpack_raw10,unpack_cv

def pack(values,padding=6):
    height,width=values.shape;stride=width*5//4+padding
    data=np.full((height,stride),197,np.uint8)
    groups=values.reshape(height,width//4,4)
    packed=data[:,:width*5//4].reshape(height,width//4,5)
    packed[:,:,:4]=groups>>2
    packed[:,:,4]=sum((groups[:,:,i]&3)<<(2*i) for i in range(4))
    return data.tobytes(),stride

class Tests(unittest.TestCase):
    def test_extreme_and_low_bits_with_padding(self):
        values=np.array([[0,1,2,3,1023,512,555,42],[4,5,6,7,255,256,257,258]],np.uint16)
        data,stride=pack(values)
        for decode in (unpack_raw10,unpack_cv):
            result=decode(data,8,2,stride)
            np.testing.assert_array_equal(result,values);self.assertEqual(result.dtype,np.uint16)
            self.assertTrue(result.flags.c_contiguous)
    def test_full_sensor_decode_preserves_every_pixel(self):
        values=np.random.default_rng(219).integers(0,1024,(1232,1640),dtype=np.uint16)
        data,stride=pack(values)
        for decode in (unpack_raw10,unpack_cv):np.testing.assert_array_equal(decode(data,1640,1232,stride),values)
    def test_invalid_layout_rejected(self):
        for width,height,stride,data in ((5,1,10,b' '*10),(8,1,9,b' '*20),(8,2,10,b' '*19)):
            with self.assertRaises(ValueError):unpack_raw10(data,width,height,stride)

if __name__=='__main__':unittest.main()
