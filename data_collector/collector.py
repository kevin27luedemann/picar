#!/usr/bin/env python3
import gpsd
import numpy as np
import h5py
import time
import datetime as dt
from picamera import PiCamera
from picamera import array
#from picamera import PiCameraCircularIO as circular

def init_gps():
    # Connect to the local gpsd
    gpsd.connect()
    #dummy read which is needed at the beginning for some reason
    collect_data()

def init_hdf5(fname):
    f               = h5py.File(fname,"w",libver="latest")
    f.swmr_mode     = True
    f.close()
    f               = h5py.File(fname,"r+",libver="latest")
    f.swmr_mode     = True
    return f

#alternatives are
#reso         = (3280,2464) #largest possible resolution (full view) of v2
#reso         = (2592, 1944)#largest possible resolution (full view) of v1
#reso         = (1920, 1080)
#reso         = (640,480)
#framerate    = 30
#framerate    = 15
def init_camera(reso=(3280,2464),framerate=10):
    camera = PiCamera()
    camera.resolution   = reso
    #Do not set the framerate for images
    #camera.framerate    = framerate

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)
    return camera

def dinit_camera(camera):
    camera.stop_preview()

def take_picture(camera):
    output      = array.PiYUVArray(camera)
    camera.capture(output, format='yuv')
    return output.array

def collect_gps_data():
    packet = gpsd.get_current()

    #initialize all values with NAN for better filtering
    data    = np.ones(6)*np.nan
    error   = np.ones(6)*np.nan

    #Set the values that are available depending on the mode
    if packet.mode >= 2:
        data[0] = packet.lat
        data[1] = packet.lon
        data[2] = packet.hspeed
        data[3] = packet.track
        error[0]= packet.error["t"]
        error[1]= packet.error["y"]
        error[2]= packet.error["x"]
        error[3]= packet.error["s"]
    if packet.mode >= 3:
        data[4] = packet.alt
        data[5] = packet.climb
        error[4]= packet.error["c"]
        error[5]= packet.error["v"]

    return packet.time,data,error

def main(camera):
    while True:
        ti,da,er    = collect_data()
        print(ti)
        if ti != '':
            #"2021-04-07T08:34:01.000Z"
            dti         = dt.datetime.strptime(ti,"%Y-%m-%dT%H:%M:%S.%fZ")
            print(dti)
            print((dti-dt.datetime(2000,1,1)).total_seconds())

        print(da)
        print(er)
        print()
        time.sleep(1)
    

if __name__ == "__main__":
    #setup is done here
    init_gps()
    cam     = init_camera()
    h5file  = init_hdf5(name)
    #Run the main loop after the setup is done
    main(cam)
    #Stop camera after all is done
    dinit_camera(cam)

