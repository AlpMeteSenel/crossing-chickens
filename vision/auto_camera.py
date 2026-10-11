"""Bounded independent shutter/gain regulation for IMX219 analogue controls."""
import math

def gain_factor(code):
    return 256/(256-code)

def auto_step(exposure, gain, level, limit, auto_exposure=True, auto_gain=True):
    if not math.isfinite(level) or not (auto_exposure or auto_gain):return exposure,gain
    ratio=max(.88,min(1.12,350/max(level,1)))
    if abs(ratio-1)<=.04:return exposure,gain
    sensitivity=exposure*gain_factor(gain)*ratio
    if auto_exposure and auto_gain:
        shutter=max(100,min(limit,round(sensitivity)))
        # Use integration first; amplify only when the selected blur limit is reached.
        analogue=max(0,min(232,round(256-256*shutter/max(sensitivity,1))))
    elif auto_exposure:
        shutter=max(100,min(limit,round(exposure*ratio)));analogue=gain
    else:
        shutter=exposure;analogue=max(0,min(232,round(256-256*exposure/max(sensitivity,1))))
    return shutter,analogue

def validate_controls(data):
    result={}
    for key in ('auto_exposure','auto_gain'):
        if key in data:
            if type(data[key]) is not bool:raise ValueError(key+' must be true or false')
            result[key]=data[key]
    for key,low,high in (('held_exposure',100,6000),('held_gain',0,232)):
        if key in data:
            if type(data[key]) is not int or not low<=data[key]<=high:raise ValueError('Invalid '+key)
            result[key]=data[key]
    return result
