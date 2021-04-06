import subprocess
import cv2
import json
import time
from brain.object_counter.tracking.objectCounter_cv_cpu import objectCounter
from django.core.management.base import BaseCommand
from vehicle_counter.models import VehicleAssessmentConfiguration

class Command(BaseCommand):
    help = 'Excecute counter!!!'

    def __init__(self):        
        self.path = 0
        self.cap = cv2.VideoCapture(self.path)
        self.rtmp_url = "rtmp://127.0.0.1:1935/live/pupils_trace"
        # gather video info to ffmpeg
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.command = ['ffmpeg',
            '-y',
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', "{}x{}".format(self.width, self.height),
            '-r', str(self.fps),
            '-i', '-',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'ultrafast',
            '-f', 'flv',
            self.rtmp_url]
        self.detector=objectCounter()
        self.polygon=json.loads(VehicleAssessmentConfiguration.objects.all().values()[0]["detection_roi"])
        print("INITIALITZING")

        
    def handle(self, *args, **kwargs):
        p = subprocess.Popen(self.command, stdin=subprocess.PIPE)
        while self.cap.isOpened():
            ret, frame = self.cap.read()

            self.polygon=json.loads(VehicleAssessmentConfiguration.objects.all().values()[0]["detection_roi"])
    
            if not ret:
                print("frame read failed")
                break

            before_detection=time.time()
            frame=self.detector.processVideoStream(self.polygon,frame)
            print(f"SPEND TIME {time.time()-before_detection} seconds",end="\r")
            # YOUR CODE FOR PROCESSING FRAME HERE

            # write to pipe
            p.stdin.write(frame.tobytes())




