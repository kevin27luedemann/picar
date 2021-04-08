#!/usr/bin/env python3
import gpsd
import numpy as np
import h5py
import time
import datetime as dt
from picamera import PiCamera
from picamera import array
#from picamera import PiCameraCircularIO as circular
import warnings
warnings.filterwarnings("ignore", message="PiCameraResolutionRounded")

def init_gps():
    # Connect to the local gpsd
    gpsd.connect()
    #dummy read which is needed at the beginning for some reason
    collect_gps_data()

def init_hdf5(fname,camera):
    f               = h5py.File(fname,"a",libver="latest")
    f.swmr_mode     = True
    #only save the Y value of YUV
    if not("/timelaps" in f):
        dummy       = take_picture(camera)
        d_pic       = f.create_dataset( "timelaps",
                                        data=[dummy],
                                        dtype="u8",
                                        compression="lzf",
                                        #compression_opts=6, #only for gzip
                                        maxshape=(  None,
                                                    dummy.shape[0],
                                                    dummy.shape[1]),
                                        chunks=True)
        #rewind to zero position
        d_pic.resize(0,axis=0)
    else:
        d_pic       = f["/timelaps"]


    if not("/GPS" in f):
        ti,da,er    = collect_gps_data()
        while ti == '':
            time.sleep(0.1)
            ti,da,er    = collect_gps_data()
        dti         = dt.datetime.strptime(ti,"%Y-%m-%dT%H:%M:%S.%fZ")
        ti_sec      = (dti-dt.datetime(2000,1,1)).total_seconds()
        dummy       = np.append(da,er,axis=0)
        dummy       = np.append(np.array([ti_sec]),dummy,axis=0)
        d_gps       = f.create_dataset( "GPS",
                                        data=[dummy],
                                        compression="gzip",
                                        compression_opts=6,
                                        maxshape=(  None,
                                                    dummy.shape[0]),
                                        chunks=True)
        d_gps.resize(0,axis=0)
    else:
        d_gps       = f["/GPS"]
    return f,d_pic,d_gps

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

def write_dset(arr,dset):
        dset.resize(dset.len()+1,axis=0)
        dset[dset.len()-1]    = arr

def take_picture(camera):
    output      = array.PiYUVArray(camera)
    camera.capture(output, format='yuv')
    return output.array[:,:,0]

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

def format_gps_data():
    ti,da,er    = collect_gps_data()
    while ti == '':
        time.sleep(0.1)
        ti,da,er    = collect_gps_data()
    dti         = dt.datetime.strptime(ti,"%Y-%m-%dT%H:%M:%S.%fZ")
    ti_sec      = (dti-dt.datetime(2000,1,1)).total_seconds()
    GPS_point   = np.append(da,er,axis=0)
    GPS_point   = np.append(np.array([ti_sec]),GPS_point,axis=0)
    return GPS_point

def main(camera,h5file,d_pic,d_gps):
    counter     = 0
    while counter < 10:
        print(counter)
        PIC         = take_picture(camera)
        if counter == 9:
            write_dset(PIC,d_pic)
        GPS_point   = format_gps_data()
        write_dset(GPS_point,d_gps)
        time.sleep(1)
        counter += 1
    
if __name__ == "__main__":
    fname               = dt.datetime.strftime( dt.datetime.now(),
                                                "%Y%m%d")+".hdf5"
    print(fname)
    #setup is done here
    init_gps()
    cam                 = init_camera()
    h5file,d_pic,d_gps  = init_hdf5(fname,cam)
    #Run the main loop after the setup is done
    main(cam,h5file,d_pic,d_gps)
    #Stop camera after all is done
    dinit_camera(cam)
    h5file.close()

