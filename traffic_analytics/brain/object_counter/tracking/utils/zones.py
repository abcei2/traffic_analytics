import cv2, numpy as np
from roipoly.roipoly import RoiPoly
from matplotlib import pyplot as plt
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

def selectPolygonZone(image,color):
    zones = []
    
    while True:
        try:
            plt.figure(figsize=(12,8))
            
            plt.imshow(image, aspect='auto',cmap = 'gray')
            zone = RoiPoly(color = color)
            zone.x[0] = zone.x[-1]
            zone.y[0] = zone.y[-1]
            zone.x = list(map(int, zone.x))
            zone.y = list(map(int, zone.y))
            polyZone = []
                        
            for point in zip(zone.x,zone.y):
                polyZone.append((point))

            pts = np.array(polyZone, np.int32)
            pts = pts.reshape((-1,1,2))

            if color == 'red':
                cv2.polylines(image,[pts],True,(255,0,0),2)
            else:
                cv2.polylines(image,[pts],True,(0,255,0),2)

        except:
            break
        zones.append(polyZone)
    cv2.destroyAllWindows()
    return zones

class designatedArea:
    def __init__(self, inputZone):
        self.zone = Polygon( [inputZone[0], inputZone[1], inputZone[2], inputZone[3]] )
        self.points = [inputZone[0], inputZone[1], inputZone[2], inputZone[3]]
        self.count = 0
        self.allowed = True

    def contains(self, inPoint):
        return self.zone.contains( Point( inPoint)  )



        

if __name__ == "__main__":
    image = cv2.imread("cam.jpg")
    point = (768, 423)

    for poly in selectPolygonZone(image,'red'):        
        print(containPoint(poly,point))
    
    #for entrada in selectInputZones(image):
    #    print(findPoint(entrada, (320, 323)))
    #selectPolygonZoneInput(image)