import cv2
import time
import os

class VideoCamera(object):
    def __init__(self):
        self.image_off=cv2.imread(f"traffic_analytics/static/img/off-air.jpg")
        self.before=time.time()
        # Using OpenCV to capture from device 0. If you have trouble capturing
        # from a webcam, comment the line below out and use a video file
        # instead.
        self.video = cv2.VideoCapture("rtmp://127.0.0.1:1935/live/pupils_trace")
        # If you decide to use video.mp4, you must have this file in the folder
        # as the main.py.
        # self.video = cv2.VideoCapture('video.mp4')
    
    def __del__(self):
        print("DELETED")
        self.video.release()
        self.get_frame(False)
    
    def get_frame(self, streaming_on):
        # print(f"time spend {time.time()-self.before}")
        self.before=time.time()
        image=[]
        if streaming_on:
            success, image = self.video.read()
            if not success:
                image=self.image_off
        else:
            image=self.image_off
        # We are using Motion JPEG, but OpenCV defaults to capture raw images,
        # so we must encode it into JPEG in order to correctly display the
        # video stream.
        ret, jpeg = cv2.imencode('.jpg', image)
        return streaming_on, jpeg.tobytes()


def gen(camera):
    while True:
        streaming_on, frame = camera.get_frame(True)

        if streaming_on:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            break
