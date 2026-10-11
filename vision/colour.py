"""Conservative linear-light IMX219 colour correction before gamma encoding.

CCM: Raspberry Pi libcamera IMX219 tuning, 4650 K. Blend with identity because
this simplified pipeline lacks that ISP's full illuminant and lens calibration.
Source: https://raw.githubusercontent.com/raspberrypi/libcamera/main/src/ipa/rpi/vc4/data/imx219.json
"""
import cv2
import numpy as np

CCM_RGB=np.array([[2.18174,-.70887,-.47287],[-.70196,2.76426,-1.06231],[-.25157,-.71978,1.97135]],dtype=np.float32)
CCM_BGR=(.45*CCM_RGB+.55*np.eye(3,dtype=np.float32))[::-1,::-1].copy()
GAMMA=(np.linspace(0,1,960,dtype=np.float32)**(1/2.2)*255).astype(np.uint8)

def render(b,g,r,gains,natural=True):
    # Preserve the sensor's 10-bit precision, using OpenCV's vectorised integer
    # kernels instead of repeated reductions over large floating-point arrays.
    channels=[cv2.subtract(c,64) for c in (b,g,r)]
    gain=np.asarray(gains,np.float32)
    matrix=CCM_BGR*gain[None,:] if natural else np.diag(gain)
    linear=cv2.transform(cv2.merge(channels),matrix)
    if natural:
        clipped=[cv2.compare(c, float(959*.95/g),cv2.CMP_GE) for c,g in zip(channels,gain)]
        highlight=cv2.bitwise_or(cv2.bitwise_and(clipped[0],clipped[1]),cv2.bitwise_or(cv2.bitwise_and(clipped[0],clipped[2]),cv2.bitwise_and(clipped[1],clipped[2])))
        # Chroma is unavailable once two balanced channels clip; neutral white
        # prevents the colour matrix creating magenta lamps. Single-channel
        # saturated reds are kept coloured.
        linear[highlight!=0]=959
    np.minimum(linear,959,out=linear)
    return GAMMA[linear]
