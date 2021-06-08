import cv2
import time
import os
import asyncio 
import numpy as np
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    MediaStreamTrack
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling, TcpSocketSignaling

import threading
import time


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track

    async def recv(self):
        
        before=time.time()
        frame = await self.track.recv()
        
        # print(frame.copy()   )
        # self.main_frame.update_frame(frame.copy())
        
        print(f"takes {time.time()-before}")
        # cv2.imshow("frame",frame.to_ndarray )
        # cv2.waitKey(10)
        return frame

async def run_loop(pc, player, recorder, signaling, relay, role, main_frame,loop):
    def add_tracks():
        if player and player.audio:
            pc.addTrack(player.audio)

        if player and player.video:
            pc.addTrack(player.video)
    
    @pc.on("track")
    def on_track(track):

        print("Receiving %s" % track.kind)
        recorder.addTrack(track)
        if track.kind == "video":
            pc.addTrack(
                VideoTransformTrack(
                    relay.subscribe(track)
                )
            )

    # connect signaling
    await signaling.connect()

    # consume signaling
    while True:
        obj = await signaling.receive()

        if isinstance(obj, RTCSessionDescription):
            await pc.setRemoteDescription(obj)
            await recorder.start()

            if obj.type == "offer":
                # send answer
                add_tracks()
                await pc.setLocalDescription(await pc.createAnswer())
                await signaling.send(pc.localDescription)
        elif isinstance(obj, RTCIceCandidate):
            await pc.addIceCandidate(obj)
        elif obj is BYE:
            print("Exiting")
            break


class VideoCamera(object):

    def __init__(self):
        
        self.image_off=cv2.imread(f"traffic_analytics/static/img/off-air.jpg")

    def __del__(self):
        print("DELETED")

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

class FrameClass(object):
    def __init__(self):
        self.frame=None
    def update_frame(self,frame):
        self.frame=frame
    def is_similar(self,actual_frame, prev_image):
        try:
            return actual_frame.shape == prev_image.shape and not(np.bitwise_xor(actual_frame,prev_image).any())
        except AttributeError as error:
            
            return False
        
       



def gen(camera):
    

    relay = MediaRelay()    
    # create signaling and peer connection
    signaling = TcpSocketSignaling("192.168.1.20", "8082")
    pc = RTCPeerConnection()

    player = None

    # create media sink
    # if args.record_to:
    #     recorder = MediaRecorder(args.record_to)
    # else:
    recorder = MediaBlackhole()
    print("creating!")

    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever).start()  
    main_frame = FrameClass()  
    future = asyncio.run_coroutine_threadsafe(run_loop(
        pc=pc,
        player=player,
        recorder=recorder,
        relay=relay,
        signaling=signaling,
        role="answer",
        main_frame=main_frame,
        loop=loop
    ), loop)
    print("pass")

    prev_image=None
    # loop.call_soon_threadsafe(loop.stop)
    
    while True:
        # streaming_on, frame = camera.get_frame(False)
        streaming_on= True
        
        if main_frame.frame:
            actual_frame=main_frame.frame.to_ndarray(format="bgr24")
            
            
            if not main_frame.is_similar(actual_frame, prev_image):   
                print(main_frame.frame)   
                  
                prev_image=actual_frame.copy()
                ret, frame=cv2.imencode('.jpg',prev_image)
                frame=frame.tobytes()
            
                if streaming_on:
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                    
                    before=time.time()
                                
        # sleep(10)
        # else:
        #     break
