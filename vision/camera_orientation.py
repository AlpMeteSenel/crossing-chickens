"""Clockwise camera orientation; normalized geometry and native crops agree."""
def validate_rotation(value):
    if type(value) is not int or value not in (0,90,180,270):
        raise ValueError('Camera rotation must be 0, 90, 180 or 270 degrees')
    return value

def rotate_point(point, degrees):
    x,y=point
    return {0:(x,y),90:(1-y,x),180:(1-x,1-y),270:(y,1-x)}[degrees%360]

def rotate_points(points, degrees):
    return [list(rotate_point(p,degrees)) for p in points] if points is not None else None

def rotate_bounds(bounds, degrees):
    x1,y1,x2,y2=bounds
    corners=rotate_points([(x1,y1),(x2,y1),(x2,y2),(x1,y2)],degrees)
    return (min(p[0] for p in corners),min(p[1] for p in corners),
            max(p[0] for p in corners),max(p[1] for p in corners))

def rotate_image(image, degrees):
    if image is None or degrees==0:return image
    import cv2
    return cv2.rotate(image,{90:cv2.ROTATE_90_CLOCKWISE,180:cv2.ROTATE_180,270:cv2.ROTATE_90_COUNTERCLOCKWISE}[degrees])

def detail_crop(camera,bounds,degrees):
    crop,actual=camera.detail_crop(rotate_bounds(bounds,-degrees))
    if crop is None or actual is None:return None,None
    return rotate_image(crop,degrees),rotate_bounds(actual,degrees)
