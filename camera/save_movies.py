import numpy as np
from picamera import PiCamera
from picamera import array
import time
from io import BytesIO

def main():
    camera = PiCamera()
    camera.resolution   = (1920, 1080)
    camera.framerate    = 30
    #camera.resolution   = (2592, 1944)
    #camera.framerate    = 15

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)
    
    #start actual recording
    camera.start_recording('my_video.mp4', format="h264")
    #camera.start_recording('my_video.mjpg')
    camera.wait_recording(10)
    camera.stop_recording()
    camera.stop_preview()

if __name__ == "__main__":
    main()
