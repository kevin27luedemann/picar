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

np.set_printoptions(threshold=sys.maxsize)

#Variable to keep main loop running until SIGINT
motion_detected     = False
keep_running        = True
debug_file          = None
flags               = None
mth_roll            = 75
mbl_roll            = 15
mth_stan            = 5
mbl_stan            = 4
#Handle the SIGINT interrupt
def signal_handler(signum, frame):
    global keep_running
    keep_running    = False

class MotionDetec(array.PiMotionAnalysis):
    def __init__(self,  camera,size=None,
                        threshold=80,
                        num_blocks=7,
                        num_no_motion_frames=30,
                        local_motion_mask=np.ones((30,40))):
        super().__init__(camera,size)
        self.no_motion_frames       = 0
        self.threshold              = threshold
        self.num_blocks             = num_blocks
        self.num_no_motion_frames   = num_no_motion_frames
        self.set_mask(local_motion_mask)
        self.lock                   = False

    def set_mask(self,mask):
        self.lock                   = True
        self.motion_mask            = mask
        self.motion_mask            = np.pad(   self.motion_mask,
                                                ((0,0),(0,1)),
                                                mode="constant",
                                                constant_values=0)
        self.lock                   = False

    def analyse(self, a):
        global motion_detected
        global flags
        global debug_file
        a = np.sqrt(np.square(a['x'].astype(float)) +
                    np.square(a['y'].astype(float)))

        while (self.lock):
            time.sleep(0.05)

        a = a*self.motion_mask

        if      not(motion_detected)    and \
                (a > self.threshold).sum() > self.num_blocks and \
                (a > self.threshold).sum() < self.motion_mask.sum()*0.8:
            motion_detected         = True
            self.no_motion_frames   = 0
            if flags[1]:
                nx,ny                       = a.shape
                debug_file.write("{}".format(dt.datetime.strftime(
                                                    dt.now(),
                                                    "%Y%m%d%H%M%S")))
                for i in range(nx):
                    for j in range(ny):
                        if j == ny-1:
                            debug_file.write("{:4.01f}\n".format(a[i,j]))
                        else:
                            debug_file.write("{:4.01f}".format(a[i,j]))
                debug_file.write("\n")

        elif    motion_detected         and \
                (a > self.threshold).sum() > self.num_blocks and \
                (a > self.threshold).sum() < self.motion_mask.sum()*0.8:
            self.no_motion_frames   = 0
            if flags[1]:
                nx,ny                       = a.shape
                for i in range(nx):
                    for j in range(ny):
                        if j == ny-1:
                            debug_file.write("{:4.01f}\n".format(a[i,j]))
                        else:
                            debug_file.write("{:4.01f}".format(a[i,j]))
                debug_file.write("\n")

        elif    motion_detected         and \
                (a > self.threshold).sum() <= self.num_blocks     and \
                self.no_motion_frames <= self.num_no_motion_frames:
            self.no_motion_frames  += 1

        elif    motion_detected         and \
                self.no_motion_frames > self.num_no_motion_frames:
            motion_detected         = False
            self.no_motion_frames   = 0

def init_camera(reso=(3280,2464),framerate=30,loglevel=2):
    camera = PiCamera()
    if camera.revision == "imx219":
        camera.resolution   = (1640,1232) 
    else:
        camera.resolution   = (1296,972) 
    camera.framerate    = framerate
    #Do not set the framerate for images
    #camera.framerate    = framerate

    #start warm up befor recording to get exposure right
    #start warmup befor recording to get exposure right
    if loglevel == 0:
        print("Starting warmup")
    camera.start_preview()
    time.sleep(2)
    if loglevel == 0:
        print("Done with warmup")

    return camera

def dinit_camera(camera):
    camera.stop_preview()

def take_picture(camera):
    output      = array.PiYUVArray(camera)
    camera.capture(output, format='yuv', use_video_port=True)
    #output      = array.PiYUVArray(camera,size=(1920,1080))
    #camera.capture(output, format='yuv', use_video_port=True,resize=(1920,1080))
    return output.array[:,:,0]

def read_status_file(name="/tmp/cam_flags"):
    flags   = np.genfromtxt(name)
    flags   = flags == 1
    return flags

def write_status_file(flgs,name="/tmp/cam_flags"):
    out         = flgs.astype("int")
    outstr      = ""
    for fl in out[:-1]:
        outstr += "{:d}\t".format(fl)
    outstr     += "{:d}".format(out[-1])
    with open(name,"w") as dafi:
        dafi.write(outstr)

def create_mask(camera,loglevel=1,praefix=""):
    if loglevel == 0:
        print("Some image will be taken")

    fname   = praefix+"mask_image"

    if loglevel == 0:
        print("Capture image")
    camera.capture(fname+".png")

    if loglevel == 0:
        print("Taking second image with 640 by 480")
    camera.capture(fname+"640_480.png",resize=(640,480))

    camera.stop_preview()

def loop(   camera,
            fname_data,
            praefix="",
            loglevel=1,
            concat=False,
            buffer_time=120,
            motion_mask=np.ones((30,40)),
            motion_mask_st=np.ones((30,40))):
    global motion_detected
    global keep_running
    global flags
    global debug_file
    global mth_stan
    global mbl_stan
    global mth_roll
    global mbl_roll

    #setting up GPS buffer
    l_data_ti       = 0.
    speed           = np.ones(30)
    counter         = 0
    standing_mode   = False

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
                            threshold=mth_roll,
                            num_blocks=mbl_roll,
                            num_no_motion_frames=camera.framerate*10,
                            local_motion_mask=motion_mask)

    camera.start_recording('/dev/null', format='h264',
                            splitter_port=2, resize=(640,480),
                            motion_output=mclass)
    
    #Do some stuff while motion is not detected and wait
    while keep_running:
        flags       = read_status_file()
        if flags[1] and debug_file == None:
            debug_file      = open("/tmp/debug_cam_motion.txt","w")
        elif not(flags[1]) and debug_file != None:
            debug_file.close()
        if flags[2]:
            fname   = "{}{}".format(praefix,dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S"))
            camera.capture("{}.jpg".format(fname), use_video_port=True)
            flags[2] = not(flags[2])
            write_status_file(flags)

        if loglevel == 0:
            print("Waiting for motion")
            print("thresh={}, num_blocks={}".format(mclass.threshold,
                                                    mclass.num_blocks))

        camera.wait_recording(0.2)
        if motion_detected or flags[0]:
            fname   = "{}{}".format(praefix,dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S"))

            if loglevel < 2:
                print("Motion at: {}".format(fname.split("/")[-1]))
            camera.split_recording("{}_during.mp4".format(fname),splitter_port=1)
            camera.capture("{}.jpg".format(fname), use_video_port=True)
            stream.copy_to("{}_before.mp4".format(fname),seconds=buffer_time)
            stream.clear()
            while (motion_detected or flags[0]) and keep_running:
                flags       = read_status_file()
                camera.wait_recording(0.5)
                #Handle GPS data once every second
                c_ti    = time.time()
                if c_ti - l_data_ti >= 1.:
                    if loglevel == 0:
                        print("counter={}".format(counter))
                    #Speed in km/h
                    with open("/tmp/gps.data","r") as dafi:
                        gps_point   = dafi.readline()
                    gps_point   = gps_point.split("\t")
                    if loglevel == 0:
                        print(gps_point)

                    try:
                        speed       = float(gps_point[-1])
                        spee        = speed
                    except:
                        if loglevel == 0:
                            print("could not Read Speed from GPS")

                    if loglevel == 0:
                        print("speed={}".format(spee))

                    if spee <= 5.0 and not(standing_mode):
                        if loglevel == 0:
                            print("Setting mode to standing mode")
                        mclass.threshold              = mth_stan
                        mclass.num_blocks             = mbl_stan
                        mclass.set_mask(motion_mask_st)
                        standing_mode                 = True
                    elif spee > 5.0 and standing_mode:
                        if loglevel == 0:
                            print("Setting mode to rolling mode")
                        mclass.threshold              = mth_roll
                        mclass.num_blocks             = mbl_roll
                        mclass.set_mask(motion_mask)
                        standing_mode                 = False

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
            #Speed in km/h
            with open("/tmp/gps.data","r") as dafi:
                gps_point   = dafi.readline()
            gps_point   = gps_point.split("\t")
            if loglevel == 0:
                print(gps_point)

            try:
                speed       = float(gps_point[-1])
                spee        = speed
            except:
                if loglevel == 0:
                    print("could not Read Speed from GPS")

            if loglevel == 0:
                print("speed={}".format(spee))

            if spee <= 5.0 and not(standing_mode):
                if loglevel == 0:
                    print("Setting mode to standing mode")
                mclass.threshold              = mth_stan
                mclass.num_blocks             = mbl_stan
                mclass.set_mask(motion_mask_st)
                standing_mode                 = True
            elif spee > 5.0 and standing_mode:
                if loglevel == 0:
                    print("Setting mode to rolling mode")
                mclass.threshold              = mth_roll
                mclass.num_blocks             = mbl_roll
                mclass.set_mask(motion_mask)
                standing_mode                 = False

            l_data_ti   = c_ti
            counter    += 1
            counter    %= 30

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
    parser.add_option(  "", "--mask_standing", dest="mask_standing",default="",
                        help="Filename for the mask image for standing")
    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")
    parser.add_option(  "-c", "--concat", dest="concat",
                        action="store_true",default=False,
                        help="Concat before and during video and delete both")
    parser.add_option(  "", "--create_mask", dest="create_mask",
                        action="store_true",default=False,
                        help="Take an image for the creation of motion mask")

    (options, args) = parser.parse_args()
    if not(os.path.isfile("/tmp/cam_flags")):
        with open("/tmp/cam_flags","w") as fi:
            fi.write("0\t0\t0")
    flags   = read_status_file()

    fname               = dt.datetime.strftime( dt.datetime.now(),"%Y%m%d")
    fname               = fname + options.postfix
    fname               = fname + ".txt"
    fname               = options.praefix + fname
    loglevel            = int(options.loglevel)

    if loglevel == 0:
        print(fname)
        print(read_status_file())

    cam                 = init_camera(loglevel=int(options.loglevel))

    if flags[1]:
        debug_file      = open("/tmp/debug_cam_motion.txt","w")
        if loglevel == 0:
            print("Debug mode active")

    if options.create_mask:
        create_mask(    cam,
                        loglevel=loglevel,
                        praefix=options.praefix)
    else:
        if options.mask != "":
            img         = Image.open(options.mask).convert('LA').resize((40,30))
            mask        = np.array(img.getdata())[:,0].reshape((30,40))
            #mask        = np.flip(mask)
            mask[mask>0]= 1.0
            if options.mask_standing != "":
                img         = Image.open(options.mask_standing).convert('LA').resize((40,30))
                mask_st     = np.array(img.getdata())[:,0].reshape((30,40))
                #mask_st     = np.flip(mask_st)
                mask_st[mask_st>0]= 1.0
            else:
                mask_st     = np.copy(mask)
        else:
            mask            = np.ones((30,40))
            mask_st         = np.ones((30,40))

        if loglevel == 0:
            print(options.mask)
            print(np.sum(mask))
            print(mask.shape)

            print(options.mask_standing)
            print(np.sum(mask_st))
            print(mask_st.shape)

        loop(   cam,
                fname,
                praefix=options.praefix,
                loglevel=loglevel,
                concat=options.concat,
                motion_mask=mask,
                motion_mask_st=mask_st)

    dinit_camera(cam)
    if debug_file != None:
        debug_file.close()
