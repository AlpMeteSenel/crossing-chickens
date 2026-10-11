"""One-shot ground calibration from the supplied 160 mm AprilTag 36h11/id 0."""
import cv2,numpy as np

SIDE_METRES=.16
class MarkerCalibration:
    def __init__(self):
        params=cv2.aruco.DetectorParameters();params.cornerRefinementMethod=cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector=cv2.aruco.ArucoDetector(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11),params)
        self.samples=[]
        self.status='Searching for AprilTag ID 0 on the ground'
    def find(self,frame):
        corners,ids,_=self.detector.detectMarkers(cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY))
        if ids is None or 0 not in ids.flatten():
            self.samples=[];self.status='Marker not found. Keep the whole black square and white border visible.';return None
        p=corners[list(ids.flatten()).index(0)].reshape(4,2)
        if min(np.linalg.norm(p-np.roll(p,1,axis=0),axis=1))<30 or abs(cv2.contourArea(p))<1200:
            self.samples=[];self.status='Marker is too small or tilted. Move it closer on the same ground plane.';return None
        h,w=frame.shape[:2];p=p/np.array([w,h])
        if self.samples and np.max(np.linalg.norm(p-self.samples[-1],axis=1))>.006:
            self.samples=[];self.status='Marker moved. Keep the camera and marker still.'
        self.samples.append(p);self.samples=self.samples[-3:]
        if len(self.samples)<3:
            self.status=f'Marker found. Checking stable corners ({len(self.samples)}/3).';return None
        self.status='Stable marker found. Saving the ground calibration.'
        return {'points':np.mean(self.samples,axis=0).tolist(),'width':SIDE_METRES,'length':SIDE_METRES,'method':'AprilTag 36h11 / ID 0'}

def marker_svg():
    pixels=cv2.aruco.generateImageMarker(cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11),0,8)
    cells=''.join(f'<rect x="{20+x*20}" y="{20+y*20}" width="20" height="20"/>' for y in range(8) for x in range(8) if pixels[y,x]==0)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="200mm" height="240mm" viewBox="0 0 200 240">
<rect width="200" height="240" fill="white"/><g fill="black">{cells}</g>
<g font-family="sans-serif" font-size="4" text-anchor="middle" fill="black">
<text x="100" y="199">SWARMFLOW · AprilTag 36h11 · ID 0</text>
<text x="100" y="207">Print at 100% / actual size. Black outer square = 160 mm.</text>
<text x="100" y="215">Verify the black edge with a ruler before calibrating.</text>
<text x="100" y="223">Place FLAT on the same ground plane as the tracked feet.</text>
<text x="100" y="231">Keep the camera fixed after calibration.</text></g></svg>'''
