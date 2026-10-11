"""Full-field IMX219 capture with controlled exposure and locked white balance."""
import os, sys, time, select, subprocess, ctypes as C, mmap, fcntl
from pathlib import Path
import cv2
import numpy as np
from colour import render
from auto_camera import auto_step,gain_factor

class PlaneMemory(C.Union):
 _fields_=[('offset',C.c_uint32),('userptr',C.c_ulong),('fd',C.c_int32)]
class Plane(C.Structure):
 _fields_=[('bytesused',C.c_uint32),('length',C.c_uint32),('m',PlaneMemory),('data_offset',C.c_uint32),('reserved',C.c_uint32*11)]
class Timeval(C.Structure):
 _fields_=[('seconds',C.c_long),('microseconds',C.c_long)]
class Timecode(C.Structure):
 _fields_=[('type',C.c_uint32),('flags',C.c_uint32),('data',C.c_uint8*8)]
class BufferMemory(C.Union):
 _fields_=[('offset',C.c_uint32),('userptr',C.c_ulong),('planes',C.POINTER(Plane)),('fd',C.c_int32)]
class Buffer(C.Structure):
 _fields_=[('index',C.c_uint32),('type',C.c_uint32),('bytesused',C.c_uint32),('flags',C.c_uint32),('field',C.c_uint32),('timestamp',Timeval),('timecode',Timecode),('sequence',C.c_uint32),('memory',C.c_uint32),('m',BufferMemory),('length',C.c_uint32),('reserved2',C.c_uint32),('request_fd',C.c_int32)]
class RequestBuffers(C.Structure):
 _fields_=[('count',C.c_uint32),('type',C.c_uint32),('memory',C.c_uint32),('capabilities',C.c_uint32),('flags',C.c_uint8),('reserved',C.c_uint8*3)]

def iowr(number,structure):return 0xc0000000|(C.sizeof(structure)<<16)|(ord('V')<<8)|number

class NativeCapture:
 """Memory-map native V4L2 buffers, avoiding per-frame pipe copies."""
 def __init__(self,device):
  self.fd=os.open(device,os.O_RDWR|os.O_NONBLOCK);self.maps=[];self.started=False
  try:
   request=RequestBuffers(count=3,type=9,memory=1)
   fcntl.ioctl(self.fd,iowr(8,RequestBuffers),request)
   for index in range(request.count):
    buffer,planes=self.make_buffer(index)
    fcntl.ioctl(self.fd,iowr(9,Buffer),buffer)
    self.maps.append(mmap.mmap(self.fd,planes[0].length,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ|mmap.PROT_WRITE,offset=planes[0].m.offset))
    self.queue(index)
   fcntl.ioctl(self.fd,0x40045612,C.c_int(9));self.started=True
  except Exception:self.release();raise
 def make_buffer(self,index=0):
  planes=(Plane*1)();buffer=Buffer(index=index,type=9,memory=1,length=1)
  buffer.m.planes=C.cast(planes,C.POINTER(Plane));return buffer,planes
 def queue(self,index):
  buffer,planes=self.make_buffer(index);fcntl.ioctl(self.fd,iowr(15,Buffer),buffer)
 def latest(self):
  if not select.select([self.fd],[],[],2)[0]:raise RuntimeError('Camera frame timeout')
  latest=None
  while True:
   buffer,planes=self.make_buffer()
   try:fcntl.ioctl(self.fd,iowr(17,Buffer),buffer)
   except BlockingIOError:break
   if latest is not None:self.queue(latest.index)
   latest=buffer
  if latest is None:raise RuntimeError('No camera buffer')
  return latest,self.maps[latest.index]
 def release(self):
  if self.started:
   try:fcntl.ioctl(self.fd,0x40045613,C.c_int(9))
   except OSError:pass
   self.started=False
  for mapping in self.maps:mapping.close()
  self.maps=[]
  if self.fd is not None:os.close(self.fd);self.fd=None

class CSICamera:
 def __init__(self):
  self.capture=None
  self.natural_colour=True;self.white_reference=None;self.colour_warning=None
  sys.path.append('/usr/lib/python3/dist-packages')
  import libcamera as lc
  manager=lc.CameraManager.singleton()
  camera=next((c for c in manager.cameras if c.properties.get(lc.properties.Model)=='imx219'),None)
  if camera is None:raise RuntimeError('IMX219 camera not found')
  camera.acquire()
  try:
   config=camera.generate_configuration([lc.StreamRole.Raw])
   config.at(0).size=lc.Size(1640,1232)
   config.validate()
   if camera.configure(config):raise RuntimeError('Camera configuration failed')
   # Configure media links and the full-array 2x2 binned mode, but do not start
   # libcamera's old software ISP, which continually overrides AWB and AGC.
  finally:camera.release()
  self.sensor=next('/dev/'+p.name for p in Path('/sys/class/video4linux').glob('v4l-subdev*') if (p/'name').read_text().startswith('imx219'))
  self.device=next('/dev/'+p.name for p in Path('/sys/class/video4linux').glob('video*') if (p/'name').read_text().strip()=='msm_vfe0_video0')
  self.exposure_profile='lowlight';self.exposure_limit=6000
  self.exposure=3300;self.gain=228;self.last_adjust=time.monotonic();self.frames=0;self.samples=[]
  self.auto_exposure=True;self.auto_gain=True
  self.native_fps=None;self.previous_sequence=None;self.previous_timestamp=None
  self._controls(vertical_blanking=5600,exposure=self.exposure,analogue_gain=self.gain)
  timing=subprocess.run(['v4l2-ctl','-d',self.sensor,'--get-ctrl=pixel_rate,horizontal_blanking'],check=True,capture_output=True,text=True,timeout=3).stdout
  values=dict(line.strip().split(': ',1) for line in timing.strip().splitlines())
  self.line_ms=(1640+int(values['horizontal_blanking']))/int(values['pixel_rate'])*1000
  subprocess.run(['v4l2-ctl','-d',self.device,'--set-fmt-video=width=1640,height=1232,pixelformat=pRAA'],check=True,capture_output=True,timeout=3)
  # Query the actual row stride, including the driver's six padding bytes.
  info=subprocess.run(['v4l2-ctl','-d',self.device,'--get-fmt-video'],check=True,capture_output=True,text=True,timeout=3).stdout
  import re
  if "'pRAA'" not in info or not re.search(r'Width/Height\s*:\s*1640/1232',info):raise RuntimeError('Unexpected native Bayer format')
  self.stride=int(re.search(r'Bytes per Line\s*:\s*(\d+)',info).group(1));self.size=self.stride*1232
  self.set_balance(np.array([1.42,.72,1.10]))
  self.capture=NativeCapture(self.device)
  self.open=True
 def _controls(self,**values):
  subprocess.run(['v4l2-ctl','-d',self.sensor,'--set-ctrl='+','.join(f'{k}={v}' for k,v in values.items())],check=True,capture_output=True,timeout=3)
 def set_balance(self,gains):
  # Keep green at unity, as in a sensor colour pipeline. Scaling every channel
  # down would darken the image and turn clipped white lights magenta.
  gains=gains/gains[1]
  self.gains=gains
  levels=np.maximum(np.arange(1024,dtype=np.float32)-64,0)/959
  self.luts=[(np.clip(levels*g,0,1)**(1/2.2)*255).astype(np.uint8) for g in gains]
 def rebalance(self):
  self.frames=0;self.samples=[]
  self.colour_warning=None
 def set_white_reference(self,point):
  self.white_reference=point
 def set_exposure_profile(self,profile):
  limit={'motion':1100,'balanced':2200,'lowlight':6000}.get(profile)
  if limit is None:raise ValueError('Unknown exposure profile')
  if profile==self.exposure_profile:return
  self.exposure_profile=profile;self.exposure_limit=limit
  self.exposure=min(self.exposure,limit)
  self._controls(exposure=self.exposure)
 def set_auto_controls(self,auto_exposure=True,auto_gain=True,held_exposure=3300,held_gain=228):
  self.auto_exposure=auto_exposure;self.auto_gain=auto_gain
  shutter=self.exposure if auto_exposure else min(held_exposure,self.exposure_limit)
  gain=self.gain if auto_gain else held_gain
  if (shutter,gain)!=(self.exposure,self.gain):
   self._controls(exposure=shutter,analogue_gain=gain);self.exposure=shutter;self.gain=gain
 @property
 def gain_x(self):return round(gain_factor(self.gain),2)
 @property
 def exposure_ms(self):
  # V4L2 pixel_rate includes the binning factor used by the driver for exposure.
  # Derive timing from controls, not delayed buffer delivery/inference FPS.
  return round(self.exposure*self.line_ms,1)
 def read(self):
  read_start=time.monotonic()
  try:buffer,mapping=self.capture.latest()
  except (OSError,RuntimeError):return False,None
  dequeued=time.monotonic()
  packed=np.frombuffer(mapping,np.uint8,count=self.size).reshape(1232,self.stride)[:,:2050].reshape(1232,410,5).astype(np.uint16)
  copy_done=time.monotonic()
  self.capture.queue(buffer.index)
  queue_done=time.monotonic()
  self.timestamp=buffer.timestamp.seconds+buffer.timestamp.microseconds/1e6
  if self.previous_timestamp is not None and self.timestamp>self.previous_timestamp and buffer.sequence>self.previous_sequence:
   measured=(buffer.sequence-self.previous_sequence)/(self.timestamp-self.previous_timestamp)
   self.native_fps=measured if self.native_fps is None else .8*self.native_fps+.2*measured
  self.previous_sequence=buffer.sequence;self.previous_timestamp=self.timestamp
  raw=np.empty((1232,410,4),np.uint16)
  for i in range(4):raw[:,:,i]=(packed[:,:,i]<<2)|((packed[:,:,4]>>(2*i))&3)
  raw=raw.reshape(1232,1640)
  self.raw=raw
  raw_done=time.monotonic()
  # Each complete RGGB cell becomes one RGB preview pixel. This preserves
  # every part of the sensor's field of view without an expensive full-size ISP.
  b=raw[1::2,1::2];r=raw[::2,::2]
  g=(raw[::2,1::2]+raw[1::2,::2])//2
  small=np.stack([b[::8,::8],g[::8,::8],r[::8,::8]],axis=2).reshape(-1,3).astype(np.float32)
  signal=np.maximum(small-64,0)
  if self.white_reference is not None:
   x,y=self.white_reference;self.white_reference=None
   cx,cy=int(x*(b.shape[1]-1)),int(y*(b.shape[0]-1))
   region=np.stack([b[max(0,cy-12):cy+13,max(0,cx-12):cx+13],g[max(0,cy-12):cy+13,max(0,cx-12):cx+13],r[max(0,cy-12):cy+13,max(0,cx-12):cx+13]],axis=2).reshape(-1,3).astype(np.float32)
   valid=(region.min(1)>95)&(region.max(1)<900)
   if np.count_nonzero(valid)>=32:
    reference=np.maximum(region[valid]-64,1).mean(0)
    self.set_balance(np.clip(reference[1]/reference,.35,4));self.frames=12;self.samples=[];self.colour_warning=None
   else:self.colour_warning='White reference is too dark or clipped. Click matte white paper under the scene lighting, not a ceiling lamp.'
  if self.frames<12:
   self.frames+=1
   # Use the brighter, unclipped reference surfaces, then lock the result.
   valid=(signal.mean(1)>80)&(small.max(1)<900)
   if np.count_nonzero(valid)>100:
    reference=signal[valid].mean(0)
    self.samples.append(np.clip(reference.mean()/np.maximum(reference,1),.45,2.5))
   if self.frames==12 and self.samples:
    self.set_balance(np.median(self.samples,axis=0))
    print('Locked raw white balance B/G/R '+str(self.gains.round(3).tolist()),flush=True)
  # Slow, bounded exposure adaptation; colour gains stay unchanged.
  now=time.monotonic()
  if now-self.last_adjust>.6:
   level=float(np.percentile(signal.mean(1),65))
   exposure,gain=auto_step(self.exposure,self.gain,level,self.exposure_limit,self.auto_exposure,self.auto_gain)
   if (exposure,gain)!=(self.exposure,self.gain):
    self._controls(exposure=exposure,analogue_gain=gain);self.exposure=exposure;self.gain=gain
   self.last_adjust=now
  meter_done=time.monotonic()
  frame=render(b,g,r,self.gains,self.natural_colour)
  completed=time.monotonic()
  self.timings={'dequeue_age_ms':round((dequeued-self.timestamp)*1000,1),
                'capture_wait_ms':round((dequeued-read_start)*1000,1),
                'unpack_ms':round((raw_done-dequeued)*1000,1),
                'mapped_copy_ms':round((copy_done-dequeued)*1000,1),
                'requeue_ms':round((queue_done-copy_done)*1000,1),
                'unpack_only_ms':round((raw_done-queue_done)*1000,1),
                'meter_ms':round((meter_done-raw_done)*1000,1),
                'colour_ms':round((completed-meter_done)*1000,1),
                'capture_process_ms':round((completed-dequeued)*1000,1),
                'capture_ready_age_ms':round((completed-self.timestamp)*1000,1),
                'sensor_fps':round(self.native_fps,1) if self.native_fps else None,
                'buffer_flags':buffer.flags}
  return True,frame
 def detail_crop(self,bounds,raw=None,gains=None,natural=None):
  """Demosaic a native-resolution ROI for detection; the preview stays full-field."""
  raw=self.raw if raw is None else raw
  gains=self.gains if gains is None else gains
  natural=self.natural_colour if natural is None else natural
  x1,y1,x2,y2=bounds;h,w=raw.shape
  left=int(x1*w)//2*2;top=int(y1*h)//2*2
  right=min(w,(int(x2*w)+1)//2*2);bottom=min(h,(int(y2*h)+1)//2*2)
  if right-left<16 or bottom-top<16:return None,None
  # OpenCV's BG conversion produces BGR for the sensor's top-left-red RGGB layout.
  bgr=cv2.cvtColor(raw[top:bottom,left:right],cv2.COLOR_BAYER_BG2BGR)
  image=render(bgr[:,:,0],bgr[:,:,1],bgr[:,:,2],gains,natural)
  return image,(left/w,top/h,right/w,bottom/h)
 def release(self):
  if self.capture:self.capture.release();self.capture=None
  self.open=False
