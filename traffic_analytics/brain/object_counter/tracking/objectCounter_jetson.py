import cv2
import os
from scipy.spatial import distance as dist
import numpy as np
import time
import sys
import json

from tracking.pyimagesearch.centroidtracker import CentroidTracker
from tracking.pyimagesearch.trackableobject import TrackableObject
from tracking.utils.zones import selectPolygonZone
from tracking.utils.zones import designatedArea

import jetson.inference
import jetson.utils
import cv2
import base64

classNames = { 0: 'background',
    1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat',
    5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat', 9: 'chair',
    10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
    14: 'motorbike', 15: 'person', 16: 'pottedplant',
    17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor' }
count_classes=[0 for i in range(len(classNames))]

class objectCounter:
    def __init__(self):
        self.peopleCount = 0
        self.outPermitedZone = False
        self.labels = ['background','person']
        self.allowedZones = []
        self.color = lambda state: (0,255,0) if (state) else (0,0,255)


        jsonpath="./tracking/data.json"
        with open(jsonpath) as data:
            DATA_INPUT = json.load(data)
        self.net = jetson.inference.detectNet("ssd-mobilenet-v2", "", 0.6)
        
        self.ZONES = [ zone for zone in DATA_INPUT['Zones'] ]


        self.allowedZones = [ designatedArea(inputZones) for inputZones in self.ZONES ]
        tracker_types = ['KCF'      , 'TLD' , 'MEDIANFLOW' , 'MOSSE']
        self.tracker_type = tracker_types[0]

        
        self.currentBoxes = []
        self.currentTypeList = []
        self.trackers = []

        self.SKIPFRAMES = 2
        self.idFrame = 1


        self.maxDistance = 120
        self.maxDistance2 = 120
        self.maxDisaperance = 6

        self.ct = CentroidTracker( self.maxDisaperance, self.maxDistance )
        # self.ct = CentroidTracker( )
        self.trackableObjects = {}

    def resetValues(self):
        self.peopleCount = 0
        self.outPermitedZone = 0
        self.labels = ['background','person']
        self.allowedZones = []


    def detectPeople(self, frame, threshold):
        before=time.time()
        frame_cuda = jetson.utils.cudaFromNumpy(frame)

        # # detect objects in the image (with overlay)
        detections = self.net.Detect(frame_cuda, overlay="box,labels,conf")
        print(f"TAKES {time.time()-before} seconds to proccess")
        return [detection.ClassID for detection in detections ], [detection.Confidence for detection in detections ],[[int(detection.Left), int(detection.Top),int(detection.Right)-int(detection.Left),int(detection.Bottom)-int(detection.Top)] for detection in detections ]
    
    def createTracker(self,tracker_type):
        
        if(tracker_type == 'KCF'):
            tracker = cv2.TrackerKCF_create()
        elif(tracker_type == 'TLD'):
            tracker = cv2.TrackerKCF_create()
        elif(tracker_type == 'MEDIANFLOW'):
            tracker = cv2.TrackerKCF_create()
        elif(tracker_type == 'MOSSE'):
            tracker = cv2.TrackerKCF_create()
        return tracker


        

    def processVideoStream(self, polygon, frame, HEAVY_TRACKER = True):
        

        frameHeight, frameWidth,_ = frame.shape

        
        self.ZONES = [
            [
                [int(polygon["x1"]*frameWidth),int(polygon["y1"]*frameHeight)],
                [int(polygon["x2"]*frameWidth),int(polygon["y2"]*frameHeight)],
                [int(polygon["x3"]*frameWidth),int(polygon["y3"]*frameHeight)],
                [int(polygon["x4"]*frameWidth),int(polygon["y4"]*frameHeight)]
            ],
            [
                [int(polygon["x1"]*frameWidth),int(polygon["y1"]*frameHeight)],
                [int(polygon["x2"]*frameWidth),int(polygon["y2"]*frameHeight)],
                [int(polygon["x3"]*frameWidth),int(polygon["y3"]*frameHeight)],
                [int(polygon["x4"]*frameWidth),int(polygon["y4"]*frameHeight)]
            ],
        ]


        self.allowedZones = [ designatedArea(inputZones) for inputZones in self.ZONES ]


        frame2show = frame.copy()

        newBoxes = []
        newTypeList = []

        if self.trackers and HEAVY_TRACKER:
            
            timeI = time.time()
            self.currentBoxes = []
            todel = []

            for i,tracker in enumerate(self.trackers):
            
                ok,objectBox = tracker.update(frame)
            
                # unpack the position object
                startX = int(objectBox[0])
                startY = int(objectBox[1])
                endX = int(objectBox[0] + objectBox[2])
                endY = int(objectBox[1] + objectBox[3])

                if(endX > frameWidth):
                    endX = frameWidth
                if(endY > frameHeight):
                    endY = frameHeight
                
                if(not ok):
                    todel.append(i)
                else:
                    newBoxes.append((startX, startY, endX, endY))
                    self.currentBoxes.append((startX, startY, endX, endY))
            for i in range( len(todel) ):
                del self.trackers[ todel[-i-1] ]
                del self.currentTypeList[ todel[-i-1] ]
        if( (self.idFrame % self.SKIPFRAMES == 0) ):
            self.idFrame = 1

            newBoxes = []
            newTypeList = []

            detClasses, detConfidences,detBoxes = self.detectPeople(frame, threshold=0.7)

            currentOutCount = 0
            for i in range( len(detBoxes) ):
                center = ( int(detBoxes[i][0] + detBoxes[i][2]/2), int(detBoxes[i][1] + detBoxes[i][3]/2) )
                if( self.allowedZones[0].contains( center ) ):
                    newBoxes.append( (detBoxes[i][0],detBoxes[i][1],detBoxes[i][0] + detBoxes[i][2], detBoxes[i][1] + detBoxes[i][3]) )
                    newTypeList.append( detClasses[i] )              
                    cv2.rectangle(frame2show, (detBoxes[i][0],detBoxes[i][1]),(detBoxes[i][0] + detBoxes[i][2], detBoxes[i][1] + detBoxes[i][3]), (0,0,255) , 1)
               
            
            self.outPermitedZone = True if currentOutCount>0 else False

            if(self.currentBoxes and HEAVY_TRACKER):
                currentCenters = []
                newCenters = []
                if(newBoxes):
                    # Centers of the old boxes (The ones currently tracked)
                    for currentBox in self.currentBoxes:
                        currentCenters.append( ( int( (currentBox[0] + currentBox[2])/2 ),int( (currentBox[1] + currentBox[3])/2 ) ) )
                    for newBox in newBoxes:
                        newCenters.append( ( int( (newBox[0] + newBox[2])/2 ),int( (newBox[1] + newBox[3])/2 ) ) )
                    
                    distMatrix = dist.cdist( np.array(currentCenters), np.array(newCenters) )
                    distRows = distMatrix.min(axis=1).argsort()
                    distCols = distMatrix.argmin(axis=1)[distRows]

                    usedRows = set()
                    usedCols = set()
                    for (dRow, dCol) in zip(distRows, distCols):
                        if dRow in usedRows or dCol in usedCols:
                            continue
                        if distMatrix[dRow,dCol] > self.maxDistance2:
                            continue
                        usedRows.add(dRow)
                        usedCols.add(dCol)

                    unusedCols = set(range(0, distMatrix.shape[1])).difference(usedCols)
                    for dCol in unusedCols:
                        tracker = self.createTracker(self.tracker_type)
                        
                        tracker.init(frame, (newBoxes[dCol][0],newBoxes[dCol][1],newBoxes[dCol][2]-newBoxes[dCol][0],newBoxes[dCol][3]-newBoxes[dCol][1]) )
                        self.trackers.append(tracker)
                        self.currentTypeList.append(newTypeList[dCol])
                        self.currentBoxes.append( newBoxes[dCol] ) 

            elif(HEAVY_TRACKER):
                for newBox, newType in zip(newBoxes, newTypeList):
               
                    tracker = self.createTracker(self.tracker_type)
                   
                    tracker.init(frame, (newBox[0],newBox[1],newBox[2]-newBox[0],newBox[3]-newBox[1]) )
                    self.trackers.append(tracker)
                    self.currentTypeList.append(newType)
                self.currentBoxes = newBoxes.copy()
            else:
                self.currentTypeList = newTypeList.copy()
                self.currentBoxes = newBoxes.copy()
        ctObjects, ctTypeObjects, ctBoxes = self.ct.update(self.currentBoxes, self.currentTypeList, frame,count_classes)
        self.peopleCount = self.ct.nextObjectID

        for ((objectID, centroid)),((_,box)) in zip( ctObjects.items(),ctBoxes.items() ):
                # check to see if a trackable object exists for the current
                # object ID
            to = self.trackableObjects.get(objectID, None)
        
            # if there is no existing trackable object, create one
            if to is None:
                to = TrackableObject(objectID, centroid, (0,255,128), ctTypeObjects[objectID], ctBoxes[objectID])


            # store the trackable object in our dictionary
            self.trackableObjects[objectID] = to

            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "{1}_{0} ".format(count_classes[to.otype],classNames[to.otype])
            for currentBox, currentType in zip(self.currentBoxes, self.currentTypeList):
                
                cv2.rectangle(frame2show, (box[0],box[1]),(box[2], box[3]), (0,255,0) , 1)
                cv2.rectangle(frame2show, (box[0],box[1]-10),(box[2], box[1] + 10), (0,255,0), -1)
                cv2.putText(frame2show, text, (box[0],box[1]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 2)

        # if(self.outPermitedZone):
        # cv2.putText(frame2show, "CROSSED THE RED LIGHT", (15,15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
       
        cv2.polylines(frame2show, [np.array(self.allowedZones[0].points)], True, self.color(self.allowedZones[0].allowed), 2)
        to_return=frame2show
        self.idFrame += 1

        return to_return

   
    
            
            




                



        




    
            




