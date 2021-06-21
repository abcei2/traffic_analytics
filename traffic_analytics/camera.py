
import requests
import json
import cv2
import time
import numpy as np
import threading
     

def get_frame(main_frame):
    cap = cv2.VideoCapture('http://localhost:8080/stream/video.mjpeg')
    
    
            
    while True:
        ret, frame=cap.read()
        
        # ret, frame=cv2.imencode('.jpg',frame)
        # frame=frame.tobytes()
        main_frame.update_frame(frame)
class FrameClass(object):
    def __init__(self):
        self.frame=None
    def update_frame(self,frame):
        self.frame=frame.copy()
    def is_similar(self,actual_frame, prev_image):
        try:
            return actual_frame.shape == prev_image.shape and not(np.bitwise_xor(actual_frame,prev_image).any())
        except AttributeError as error:
            
            return False

main_frame=FrameClass()
x = threading.Thread(target=get_frame,args=(main_frame,))
x.start()
def gen():
    
    prev_image=None
    same_image= True
    
    before=time.time()
    while True:
        
        actual_frame=main_frame.frame.copy()
        
        if not main_frame.is_similar(actual_frame, prev_image):  
            same_image=False
            prev_image=actual_frame.copy()
            ret, frame=cv2.imencode('.jpg',prev_image)
            frame=frame.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    
            # print(f"takes {time.time()-before}")
        else:
            if not same_image:
                # before=time.time()
                same_image=True