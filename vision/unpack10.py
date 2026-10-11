"""Lossless MIPI RAW10 unpacking; retain row padding and all native pixels."""
import numpy as np

def unpack_raw10(data,width,height,stride):
    if width%4 or stride<width*5//4 or len(data)<stride*height:raise ValueError('Invalid RAW10 layout')
    packed=np.frombuffer(data,np.uint8,count=stride*height).reshape(height,stride)[:,:width*5//4].reshape(height,width//4,5)
    raw=packed[:,:,:4].astype(np.uint16)
    raw <<= 2
    lower=np.right_shift(packed[:,:,4:5],np.array([0,2,4,6],np.uint8)).astype(np.uint16)
    lower &= 3
    raw |= lower
    return raw.reshape(height,width)

def unpack_cv(data,width,height,stride):
    import cv2
    packed=np.frombuffer(data,np.uint8,count=stride*height).reshape(height,stride)[:,:width*5//4].reshape(height,width//4,5)
    high=np.empty((height,width//4,4),np.uint8)
    cv2.mixChannels([packed],[high],[0,0,1,1,2,2,3,3])
    high=cv2.multiply(high,(4,4,4,4),dtype=cv2.CV_16U)
    low=packed[:,:,4]
    bits=[cv2.multiply(cv2.bitwise_and(low,3<<(2*i)),1/(1<<(2*i))) for i in range(4)]
    return cv2.add(high,cv2.merge(bits),dtype=cv2.CV_16U).reshape(height,width)
