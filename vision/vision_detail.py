"""Focused full-resolution detection with global coordinates and duplicate removal."""
def focus_bounds(zone):
    if not zone:return None
    xs,ys=zip(*zone)
    # The chosen zone describes feet on the road. Include the body above the zone.
    return (max(0,min(xs)-.08),max(0,min(ys)-.32),min(1,max(xs)+.08),min(1,max(ys)+.08))

def tile_bounds(count=2):
    """20% overlap retains objects around seams; always retain a full-view pass."""
    if count==2:return [(0,0,.6,1),(.4,0,1,1)]
    if count==4:return [(x,y,x+.6,y+.6) for y in (0,.4) for x in (0,.4)]
    raise ValueError('Tile count must be 2 or 4')

def sweep_bounds(count,sequence):
    """One same-frame native tile per inference step, bounding camera latency."""
    plan=tile_bounds(count)
    return [plan[sequence%len(plan)]]

def map_crop(detections,bounds,crop_shape,frame_shape,classes=('person',)):
    ch,cw=crop_shape[:2];fh,fw=frame_shape[:2]
    left,top,right,bottom=bounds;result=[]
    for d in detections:
        if classes is not None and d['cls'] not in classes:continue
        a,b,c,e=d['box']
        # Cropped heads/feet create unstable ground points; discard boundary fragments.
        if (b<2 and top>0) or (e>ch-2 and bottom<.999) or e-b<10:continue
        if (a<2 and left>0) or (c>cw-2 and right<.999):continue
        result.append(dict(d,box=[(left+a/cw*(right-left))*fw,(top+b/ch*(bottom-top))*fh,
                                 (left+c/cw*(right-left))*fw,(top+e/ch*(bottom-top))*fh],detail=True))
    return result

def merge_detections(detections):
    kept=[]
    for d in sorted(detections,key=lambda d:d['conf'],reverse=True):
        a=d['box'];duplicate=False
        for k in kept:
            if k['cls']!=d['cls']:continue
            b=k['box'];intersection=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
            aa=(a[2]-a[0])*(a[3]-a[1]);ab=(b[2]-b[0])*(b[3]-b[1])
            if intersection/max(aa+ab-intersection,1e-9)>.35 or intersection/max(min(aa,ab),1e-9)>.65:
                duplicate=True;break
        if not duplicate:kept.append(d)
    return kept
