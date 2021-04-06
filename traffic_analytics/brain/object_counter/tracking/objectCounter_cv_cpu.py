'''
CENTROIDTRACKER SAVES THE OBJECT WHEN IN AND OUT!
'''

import cv2
import os
from scipy.spatial import distance as dist
import numpy as np
import time
import sys
import json

from brain.object_counter.tracking.pyimagesearch.centroidtracker import CentroidTracker
from brain.object_counter.tracking.pyimagesearch.trackableobject import TrackableObject
from brain.object_counter.tracking.utils.zones import selectPolygonZone
from brain.object_counter.tracking.utils.zones import designatedArea

import cv2
import base64

classNames = { 0: 'background',
    1: 'aeroplane', 2: 'bicycle', 3: 'bird', 4: 'boat',
    5: 'bottle', 6: 'bus', 7: 'car', 8: 'cat', 9: 'chair',
    10: 'cow', 11: 'diningtable', 12: 'dog', 13: 'horse',
    14: 'motorbike', 15: 'person', 16: 'pottedplant',
    17: 'sheep', 18: 'sofa', 19: 'train', 20: 'tvmonitor' }
count_classes=[0 for i in range(len(classNames))]

PARENT_FOLDER="./traffic_analytics/static/AI_models/object_counter/"
class objectCounter:
    def __init__(self):

      
        self.peopleCount = 0
        self.outPermitedZone = False
        self.labels = ['background','person']
        self.allowedZones = []
        self.color = lambda state: (0,255,0) if (state) else (0,0,255)


        self.net = cv2.dnn.readNetFromCaffe(f"{PARENT_FOLDER}MobilNet_SSD_opencv/MobileNetSSD_deploy.prototxt", f"{PARENT_FOLDER}/MobilNet_SSD_opencv/MobileNetSSD_deploy.caffemodel")
        
        self.ZONES = [ zone for zone in [[[312, 87], [465, 440], [638, 323], [450, 24]]] ]


        self.allowedZones = [ designatedArea(inputZones) for inputZones in self.ZONES ]
        tracker_types = ['KCF'      , 'TLD' , 'MEDIANFLOW' , 'MOSSE']
        self.tracker_type = tracker_types[0]

        
        self.currentBoxes = []
        self.currentTypeList = []
        self.trackers = []

        self.SKIPFRAMES = 1
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
        frame_resized = cv2.resize(frame,(300,300)) # resize frame for
        # frame_resized=frame.copy()
        blob = cv2.dnn.blobFromImage(frame_resized, 0.007843, (frame_resized.shape[0], frame_resized.shape[1]), (127.5, 127.5, 127.5), False)
        # detect objects in the image (with overlay)
        self.net.setInput(blob)
        #Prediction of network
        detections = self.net.forward()
        ClassID=[]
        Confidence_array=[]
        boundingboxs=[]
        #Size of frame resize (300x300)
        cols = frame_resized.shape[1] 
        rows = frame_resized.shape[0]
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2] #Confidence of prediction 
            if confidence > threshold: # Filter prediction 
                class_id = int(detections[0, 0, i, 1]) # Class label

                ClassID.append(class_id)
                Confidence_array.append(confidence)
                # Object location 
                xLeft = int(detections[0, 0, i, 3] * cols) 
                yBottom = int(detections[0, 0, i, 4] * rows)
                xRight   = int(detections[0, 0, i, 5] * cols)
                yTop   = int(detections[0, 0, i, 6] * rows)
                # Factor for scale to original size of frame
                
                heightFactor = frame.shape[0]/300.0  
                widthFactor = frame.shape[1]/300.0 
                # Scale object detection to frame
                xLeft = int(widthFactor * xLeft) 
                yBottom = int(heightFactor * yBottom)
                xRight   = int(widthFactor * xRight)
                yTop   = int(heightFactor * yTop)
                boundingboxs.append([int(xLeft), int(yBottom),
                    abs(int(xRight)-int(xLeft)),abs(int(yBottom)-int(yTop))])
        #print(f"TAKES {time.time()-before} seconds to proccess")
        return ClassID, Confidence_array, boundingboxs
    
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


        

    def processVideoStream(self, polygon, frame, HEAVY_TRACKER = False):
        


        to_return={"image":"","status":400}
        
        frameHeight, frameWidth,_ = frame.shape

        
        self.ZONES = [
            [
                [int(polygon[0]["x"]*frameWidth),int(polygon[0]["y"]*frameHeight)],
                [int(polygon[1]["x"]*frameWidth),int(polygon[1]["y"]*frameHeight)],
                [int(polygon[2]["x"]*frameWidth),int(polygon[2]["y"]*frameHeight)],
                [int(polygon[3]["x"]*frameWidth),int(polygon[3]["y"]*frameHeight)]
            ]
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
        # cv2.polylines(frame2show, [np.array(self.allowedZones[1].points)], True, self.color(self.allowedZones[1].allowed), 2)
        # cv2.imshow('peopleCounter', frame2show)

        to_return=frame2show

        self.idFrame += 1

     
        return to_return

   
    
            
            




                



        




    
            




