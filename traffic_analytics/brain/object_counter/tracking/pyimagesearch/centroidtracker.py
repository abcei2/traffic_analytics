# import the necessary packages
'''
	HERE WE UPDATE DATABASE BECAUSE IS THE LAST TIME WE SAW THE VEHICLE
	Look for deregister and register function
'''
from scipy.spatial import distance as dist
from collections import OrderedDict
import numpy as np
from brain.db_utils.object_counter_querys import count_object
#from shapely.geometry.polygon import Polygon

m2 = (120-50)/(431-183)
radius = lambda y: m2*y

class CentroidTracker:
	def __init__(self, maxDisappeared=50, maxDistance=30, singleTypes=None, SAVE_DETS = False, SAVE_PATH = None):
		
		# initialize the next unique object ID along with two ordered
		# dictionaries used to keep track of mapping a given object
		# ID to its centroid and number of consecutive frames it has
		# been marked as "disappeared", respectively
		self.nextObjectID = 0
		self.objects = OrderedDict()
		self.boxes = OrderedDict()
		self.objectsTypes = OrderedDict()
		self.disappeared = OrderedDict()


		self.SAVE_DETS = SAVE_DETS
		self.SAVE_PATH = SAVE_PATH

		if(SAVE_PATH == None):
			self.SAVE_DETS = False

		self.singleTypes = singleTypes
		if self.singleTypes:
			self.vehicleCount = []
			for vtype in singleTypes:
				self.vehicleCount.append(0)
		else:
			self.vehicleCount = 0

		# store the number of maximum consecutive frames a given
		# object is allowed to be marked as "disappeared" until we
		# need to deregister the object from tracking
		self.maxDisappeared = maxDisappeared

		# store the maximum distance between centroids to associate
		# an object -- if the distance is larger than this maximum
		# distance we'll start to mark the object as "disappeared"
		self.maxDistance = maxDistance

	def register(self, centroid,objectType, box, frame):
		

		# when registering an object we use the next available object
		# ID to store the centroid

		obj_tosave = '{}_{}'.format(objectType,self.nextObjectID)
		print("{} personas".format(self.nextObjectID+1) )

		#if self.SAVE_DETS: 2DO
			
		
		if self.singleTypes:
			for i,vtype in enumerate(self.singleTypes):
				if(objectType == vtype):
					self.vehicleCount[i] += 1
		

		self.objects[self.nextObjectID] = centroid
		self.boxes[self.nextObjectID] = box
		self.objectsTypes[self.nextObjectID] = objectType
		self.disappeared[self.nextObjectID] = 0
		self.nextObjectID += 1




	def deregister(self, objectID,count_classes):

		# HERER!
		print("LEFT ",self.objectsTypes[objectID],self.disappeared[objectID],self.boxes[objectID])
		# to deregister an object ID we delete the object ID from
		# both of our respective dictionaries
		count_classes[self.objectsTypes[objectID]]+=1
		del self.objects[objectID]
		del self.boxes[objectID]
		del self.objectsTypes[objectID]
		del self.disappeared[objectID]

	def update(self, rects,objectTypesList, frame,count_classes):
		# check to see if the list of input bounding box rectangles
		# is empty
		

		if len(rects) == 0:
			# loop over any existing tracked objects and mark them
			# as disappeared
			for objectID in list(self.disappeared.keys()):
				self.disappeared[objectID] += 1
				# if we have reached a maximum number of consecutive
				# frames where a given object has been marked as
				# missing, deregister it
				if self.disappeared[objectID] > self.maxDisappeared:
					self.deregister(objectID,count_classes)
			
			# return early as there are no centroids or tracking info
			# to update
			return self.objects, self.objectsTypes, self.boxes

		# initialize an array of input centroids for the current frame
		inputCentroids = np.zeros((len(rects), 2), dtype="int")
		
		# loop over the bounding box rectangles
		for (i, (startX, startY, endX, endY)) in enumerate(rects):
			# use the bounding box coordinates to derive the centroid
			cX = int((startX + endX) / 2.0)
			cY = int((startY + endY) / 2.0)
			inputCentroids[i] = (cX, cY)		

		# if we are currently not tracking any objects take the input
		# centroids and register each of them
		if len(self.objects) == 0:
			print("HEREEEEEEEEE",objectTypesList)
			for i in range(0, len(inputCentroids)):
				self.register(inputCentroids[i],objectTypesList[i], rects[i], frame)

		# otherwise, are are currently tracking objects so we need to
		# try to match the input centroids to existing object
		# centroids
		else:
			# grab the set of object IDs and corresponding centroids
			objectIDs = list(self.objects.keys())
			objectCentroids = list(self.objects.values())
			# compute the distance between each pair of object
			# centroids and input centroids, respectively -- our
			# goal will be to match an input centroid to an existing
			# object centroid
			D = dist.cdist(np.array(objectCentroids), inputCentroids)
			# in order to perform this matching we must (1) find the
			# smallest value in each row and then (2) sort the row
			# indexes based on their minimum values so that the row
			# with the smallest value as at the *front* of the index
			# list
			rows = D.min(axis=1).argsort()
			# next, we perform a similar process on the columns by
			# finding the smallest value in each column and then
			# sorting using the previously computed row index list
			cols = D.argmin(axis=1)[rows]

			# in order to determine if we need to update, register,
			# or deregister an object we need to keep track of which
			# of the rows and column indexes we have already examined
			usedRows = set()
			usedCols = set()

			# loop over the combination of the (row, column) index
			# tuples
			for (row, col) in zip(rows, cols):
				# if we have already examined either the row or
				# column value before, ignore it
				if row in usedRows or col in usedCols:
					continue

				# if the distance between centroids is greater than
				# the maximum distance, do not associate the two
				# centroids to the same object

				objectID = objectIDs[row]
				
				gav = 0

				#if D[row, col] > radius( self.objects[objectID][1] ):
				#	continue

				if D[row, col] > self.maxDistance:
					continue

				# otherwise, grab the object ID for the current row,
				# set its new centroid, and reset the disappeared
				# counter


				self.objects[objectID] = inputCentroids[col]
				self.boxes[objectID] = rects[col]
				#self.objectsTypes[objectID] = objectTypesList[col]
				self.disappeared[objectID] = 0

				# indicate that we have examined each of the row and
				# column indexes, respectively
				usedRows.add(row)
				usedCols.add(col)

			# compute both the row and column index we have NOT yet
			# examined
			unusedRows = set(range(0, D.shape[0])).difference(usedRows)
			unusedCols = set(range(0, D.shape[1])).difference(usedCols)

			# in the event that the number of object centroids is
			# equal or greater than the number of input centroids
			# we need to check and see if some of these objects have
			# potentially disappeared
			if D.shape[0] >= D.shape[1]:
				# loop over the unused row indexes
				for row in unusedRows:
					# grab the object ID for the corresponding row
					# index and increment the disappeared counter
					objectID = objectIDs[row]
					self.disappeared[objectID] += 1

					# check to see if the number of consecutive
					# frames the object has been marked "disappeared"
					# for warrants deregistering the object
					if self.disappeared[objectID] > self.maxDisappeared:
						self.deregister(objectID,count_classes)

			# otherwise, if the number of input centroids is greater
			# than the number of existing object centroids we need to
			# register each new input centroid as a trackable object
			else:
				for col in unusedCols:
					self.register(inputCentroids[col],objectTypesList[col],rects[col], frame)

		# return the set of trackable objects
		return self.objects, self.objectsTypes, self.boxes