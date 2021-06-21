import cv2
import time
import os
import asyncio 
import sys
import numpy as np
from aiortc import (
    RTCIceCandidate,
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    MediaStreamTrack
)
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder, MediaRelay
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling, CopyAndPasteSignaling, object_from_string, object_to_string
import threading


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, main_frame):
        super().__init__()  # don't forget this!
        self.track = track
        self.main_frame = main_frame

    async def recv(self):
        
        before=time.time()
        frame = await self.track.recv()
        
        # print(frame.copy()   )

        
        print(f"takes {time.time()-before}")
        
        self.main_frame.update_frame(frame)
        
        return frame

async def run_loop(pc, player, recorder, signaling, relay, role, main_frame):
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
                    relay.subscribe(track), main_frame
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
        
       

class OwnCopyPaste(CopyAndPasteSignaling):

    def __init__(self):
        self._read_pipe = sys.stdin
        self._read_transport = None
        self._reader = None
        self._write_pipe = sys.stdout

    async def connect(self):
        loop = asyncio.get_event_loop()
        self._reader = asyncio.StreamReader(loop=loop)
        self._read_transport, _ = await loop.connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(self._reader), self._read_pipe
        )
        print("-- CONNECTED --")

    async def close(self):
        if self._reader is not None:
            await self.send(BYE)
            self._read_transport.close()
            self._reader = None
            print("-- DISCONNECTED --")

    async def receive(self):
        print("-- Please enter a message from remote party --")
        data = await self._reader.readline() #OBTAIN OFFER
        print()
        return object_from_string(data.decode(self._read_pipe.encoding))
        

    async def send(self, descr):
        print("-- Please send this message to remote party  --")
        self._write_pipe.write(object_to_string(descr) + "\n")
        self._write_pipe.flush()
        print()

class RunAsync(threading.Thread):
   def __init__(self, main_frame):
      threading.Thread.__init__(self)
      self.main_frame = main_frame
      
   def run(self):
        relay = MediaRelay()    
        # create signaling and peer connection
        signaling = OwnCopyPaste()
        pc = RTCPeerConnection()

        player = None

        # create media sink
        # if args.record_to:
        #     recorder = MediaRecorder(args.record_to)
        # else:
        recorder = MediaBlackhole()
        print("creating!")

        
        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_loop(
            pc=pc,
            player=player,
            recorder=recorder,
            relay=relay,
            signaling=signaling,
            role="answer",
            main_frame=self.main_frame,
        ))
        

     

def gen():
    
    main_frame = FrameClass()  
    conect_to_peer=RunAsync(main_frame)
    conect_to_peer.start()
    

    prev_image=None
    # loop.call_soon_threadsafe(loop.stop)
    print("asdfasd")
    while True:
        # streaming_on, frame = camera.get_frame(False)
        streaming_on= True
        if main_frame.frame:
            actual_frame=main_frame.frame.to_ndarray(format="bgr24")
            # print(main_frame.frame)
            
            if not main_frame.is_similar(actual_frame, prev_image):   
                # print(main_frame.frame)   
                  
                prev_image=actual_frame.copy()
                ret, frame=cv2.imencode('.jpg',prev_image)
                frame=frame.tobytes()
            
                if streaming_on:
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
                    
                    before=time.time()
        time.sleep(0.1)
                                
        # sleep(10)
        # else:
        #     break
