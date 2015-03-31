import math 
import random 

def map_dist(long1, lat1, long2, lat2):
    '''distance between 2 points on sphere surface, in meter'''
    if long1 == long2 and lat1 == lat2:
        return 0
    else:
        try:
            return 6378137*math.acos(math.sin(math.radians(lat1))*math.sin(math.radians(lat2))+math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(long2-long1)))
        except Exception,ex:
            print Exception,":",ex
            return 1000000

def is_line_segment_intersects_box(x1, y1, x2, y2, xTL, yTL, xBR, yBR):
    #Let the segment endpoints be p1=(x1 y1) and p2=(x2 y2). 
    #Let the rectangle's corners be (xTL yTL) and (xBR yBR).
    #All in lon lat

    # test 4 corners of the rectangle to see whether they are all above or below the lin
    #print 'x1, y1, x2, y2, xTL, yTL, xBR, yBR:',x1, y1, x2, y2, xTL, yTL, xBR, yBR

    f = lambda x,y: (y2-y1)*x + (x1-x2)*y + (x2*y1-x1*y2)
    f1 = f(xTL, yTL)
    f2 = f(xTL, yBR)
    f3 = f(xBR, yTL)
    f4 = f(xBR, yBR)
    if f1 > 0 and f2 > 0 and f3 > 0 and f4 > 0:
        return False # no intersection (rectangle if above line).
    if f1 < 0 and f2 < 0 and f3 < 0 and f4 < 0:
        return False # no intersection (rectangle if below line).
    if x1 > xBR and x2 > xBR:
        return False # no intersection (line is to right of rectangle). 
    if x1 < xTL and x2 < xTL:
        return False # no intersection (line is to left of rectangle). 
    #if y1 < yBR and y2 < yBR:
    if y1 > yBR and y2 > yBR:
        return False # no intersection (line is below rectangle). 
    #if y1 > yTL and y2 > yTL:
    if y1 < yTL and y2 < yTL:
        return False # no intersection (line is above rectangle). 
    return True

def rand_color():
    r = random.randint(0,255)
    g = random.randint(0,255)
    b = random.randint(0,255)
    return "#%02x%02x%02x" % (r, g, b)

def line_segment_cross(x0, y0, x1, y1, x2, y2, x3, y3):
    if (x0 == x2 and y0 == y2) or (x0 == x3 and y0 == y3): 
        return x0, y0
    if (x1 == x2 and y1 == y2) or (x1 == x3 and y1 == y3): 
        return x1, y1
    # http://en.wikipedia.org/wiki/Line-line_intersection
    p = (x0-x1)*(y2-y3)-(y0-y1)*(x2-x3)
    if p == 0:
        return None, None   # parallel

    px = ((x0*y1 - y0*x1) * (x2 - x3) - (x0 - x1) * (x2 * y3 - y2 * x3)) / p
    py = ((x0*y1 - y0*x1) * (y2 - y3) - (y0 - y1) * (x2 * y3 - y2 * x3)) / p
    if x1 != x0:
        t = (px - x0) / (x1 - x0)
    else:
        t = (py - y0) / (y1 - y0)
    if x2 != x3:
        u = (px - x2) / (x3 - x2)
    else:
        u = (py - y2) / (y3 - y2)
    if t<0 or t>1 or u<0 or u>1:
        return None, None   # intersection point is not on the segment
    return px, py

def is_in_bbox(bbox, x, y):
    return bbox[0] <= x and bbox[2] > x and bbox[1] <= y and bbox[3] > y

def lineMagnitude (x1, y1, x2, y2):
    lineMagnitude = math.sqrt(math.pow((x2 - x1), 2)+ math.pow((y2 - y1), 2))
    return lineMagnitude

def DistancePointLine (px, py, x1, y1, x2, y2):
    #http://local.wasp.uwa.edu.au/~pbourke/geometry/pointline/source.vba
    LineMag = lineMagnitude(x1, y1, x2, y2)
    if LineMag < 0.00000001:
        DistancePointLine = 9999999.0
        return DistancePointLine, x1, y1

    u1 = (((px - x1) * (x2 - x1)) + ((py - y1) * (y2 - y1)))
    u = u1 / (LineMag * LineMag)
    if (u < 0.00001) or (u > 1):
        #// closest point does not fall within the line segment, take the shorter distance
        #// to an endpoint
        ix = lineMagnitude(px, py, x1, y1)
        iy = lineMagnitude(px, py, x2, y2)
        if ix > iy:
            return iy, x2, y2
        else:
            return ix, x1, y1
    else:
        # Intersecting point is on the line, use the formula
        ix = x1 + u * (x2 - x1)
        iy = y1 + u * (y2 - y1)
        DistancePointLine = lineMagnitude(px, py, ix, iy)
    return DistancePointLine, ix, iy
    
def hsv2rgb(h, s, v):
    h = float(h)
    s = float(s)
    v = float(v)
    h60 = h / 60.0
    h60f = math.floor(h60)
    hi = int(h60f) % 6
    f = h60 - h60f
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = 0, 0, 0
    if hi == 0: r, g, b = v, t, p
    elif hi == 1: r, g, b = q, v, p
    elif hi == 2: r, g, b = p, v, t
    elif hi == 3: r, g, b = p, q, v
    elif hi == 4: r, g, b = t, p, v
    elif hi == 5: r, g, b = v, p, q
    r, g, b = int(r * 255), int(g * 255), int(b * 255)
    return r, g, b