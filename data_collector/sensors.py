#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", message="PiCameraResolutionRounded")
import gpsd
import numpy as np
import h5py
import time
import signal,os,sys
import datetime as dt
from datetime import timedelta as tidt
from io import BytesIO
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
from optparse import OptionParser
from PIL import Image

#Add sensor to path
sys.path.append("/home/pi/Documents/picar/sense_hat/")
import ICM20948 as sense

np.set_printoptions(threshold=sys.maxsize)

#Variable to keep main loop running until SIGINT
keep_running        = True
#Handle the SIGINT interrupt
def signal_handler(signum, frame):
    global keep_running
    keep_running    = False

def loop(   fname_data,
            sensor,
            praefix="",
            loglevel=1,
            concat=False,
            buffer_time=120,
            motion_mask=np.ones((40,30))):

    global keep_running

    #setting up GPS buffer
    l_data_ti       = 0.
    GPS_point       = format_gps_data()
    speed           = np.ones(30)
    counter         = 0
    fi_data         = open(fname_data,"a")

    #Use circular io buffor
    if loglevel == 0:
        print("Create 10 seconds circular io buffer and start recording h264")
    stream              = circular(camera, seconds=buffer_time)
    camera.start_recording(stream, format="h264")

    #Perform motion analysis from second splitter port with lowest resolution.
    #Reson is performance and enhanced noise removal
    if loglevel == 0:
        print("Set up motion detection on 640x480 resolution")
    mclass = MotionDetec(   camera,
                            size=(640,480),
                            num_no_motion_frames=camera.framerate*5,
                            local_motion_mask=motion_mask)

    camera.start_recording('/dev/null', format='h264',
                            splitter_port=2, resize=(640,480),
                            motion_output=mclass)
    
    #Do some stuff while motion is not detected and wait
    #start   = dt.now()
    #while dt.now()-start < tidt(seconds=30.):
    while keep_running:
        if loglevel == 0:
            print("Waiting for motion")
            print("thresh={}, num_blocks={}".format(mclass.threshold,
                                                    mclass.num_blocks))

        camera.wait_recording(0.5)
        if motion_detected:
            fname   = "{}{}".format(praefix,dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S"))
            if loglevel < 2:
                print("Motion at: {}".format(fname.split("/")[-1]))
            camera.split_recording("{}_during.mp4".format(fname),splitter_port=1)
            stream.copy_to("{}_before.mp4".format(fname),seconds=buffer_time)
            stream.clear()
            while motion_detected:
                camera.wait_recording(0.5)
                #Handle GPS and sensor data once every second
                c_ti    = time.time()
                if c_ti - l_data_ti >= 1.:
                    if loglevel == 0:
                        print("counter={}".format(counter))
                    GPS_point       = format_gps_data()
                    #Speed in km/h
                    speed[counter]  = GPS_point[3]*3.6
                    spee        = np.mean(speed)
                    if loglevel == 0:
                        print("speed={}".format(spee))

                    if spee <= 5.0:
                        mclass.threshold              = 25
                        mclass.num_blocks             = 3
                    else:
                        mclass.threshold              = 80
                        mclass.num_blocks             = 7

                    out = ""
                    for da in GPS_point:
                        out += "{}\t".format(da)

                    sensor.icm20948_Gyro_Accel_Read()
                    gs      = np.copy(sense.Accel)/16384

                    for g in gs:
                        out += "{}\t".format(g)

                    out += "\n"
                    if loglevel == 0:
                        print(out)
                    fi_data.write(out)
                    fi_data.flush()

                    l_data_ti   = c_ti
                    counter    += 1
                    counter    %= 30
            if loglevel == 0:
                print("Motion done, splitting back to circular io")
            camera.split_recording(stream,splitter_port=1)

            command = "ffmpeg -f concat -safe 0 -i {}_cat.txt -c copy {}.mp4 1> /dev/null 2> /dev/null && ".format(fname,fname)
            command += "rm -f {}_before.mp4 && ".format(fname)
            command += "rm -f {}_during.mp4 && ".format(fname)
            command += "rm -f {}_cat.txt &".format(fname)
            if loglevel == 0:
                print(command)
            with open("{}_cat.txt".format(fname),"w") as fi:
                fi.write("file '{}_before.mp4'\n".format(fname))
                fi.write("file '{}_during.mp4'\n".format(fname))
                fi.write("#{}".format(command))
            #Only run this line if you have enough CPU grunt
            if concat:
                if loglevel == 0:
                    print("Running ffmpeg command")
                os.system(command)

        #Handle GPS data once every second
        c_ti    = time.time()
        if c_ti - l_data_ti >= 1.:
            if loglevel == 0:
                print("counter={}".format(counter))
            GPS_point       = format_gps_data()
            #Speed in km/h
            speed[counter]  = GPS_point[3]*3.6
            spee        = np.mean(speed)
            if loglevel == 0:
                print("speed={}".format(spee))

            if spee <= 5.0:
                mclass.threshold              = 25
                mclass.num_blocks             = 3
            else:
                mclass.threshold              = 80
                mclass.num_blocks             = 7

            out = ""
            for da in GPS_point:
                out += "{}\t".format(da)

            sensor.icm20948_Gyro_Accel_Read()
            gs      = np.copy(sense.Accel)/16384

            for g in gs:
                out += "{}\t".format(g)

            out += "\n"

            if loglevel == 0:
                print(out)
            fi_data.write(out)
            fi_data.flush()

            l_data_ti   = c_ti
            counter    += 1
            counter    %= 30

    fi_data.close()
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()

if __name__ == "__main__":
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = OptionParser()

    parser.add_option(  "-f", "--praefix", dest="praefix",default="",
                        help="File praefix and folder localtion")
    parser.add_option(  "", "--postfix", dest="postfix",
                        default="",
                        help="Specify custom input file postfix")
    parser.add_option(  "-m", "--mask", dest="mask",default="",
                        help="Filename for the mask image")
    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")
    parser.add_option(  "-c", "--concat", dest="concat",
                        action="store_true",default=False,
                        help="Concat before and during video and delete both")
    parser.add_option(  "", "--create_mask", dest="create_mask",
                        action="store_true",default=False,
                        help="Take an image for the creation of motion mask")

    (options, args) = parser.parse_args()

    fname               = dt.datetime.strftime( dt.datetime.now(),"%Y%m%d")
    fname               = fname + options.postfix
    fname               = fname + ".txt"
    fname               = options.praefix + fname

    if options.loglevel == 0:
        print(fname)

    sensor              = sense.ICM20948()
    init_gps()
    cam                 = init_camera(loglevel=int(options.loglevel))

    if options.create_mask:
        create_mask(    cam,
                        loglevel=int(options.loglevel),
                        praefix=options.praefix)
    else:
        if options.mask != "":
            img         = Image.open(options.mask).convert('LA').resize((40,30))
            mask        = np.array(img.getdata())[:,0].reshape((40,30))
            mask        = np.flip(mask)
            mask[mask>0]= 1.0
        else:
            mask        = np.ones((40,30))

        loop(   cam,
                fname,
                sensor,
                praefix=options.praefix,
                loglevel=int(options.loglevel),
                concat=options.concat,
                motion_mask=mask)
    dinit_camera(cam)
