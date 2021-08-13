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
from optparse import OptionParser
from PIL import Image

np.set_printoptions(threshold=sys.maxsize)

#Variable to keep main loop running until SIGINT
keep_running        = True
#Handle the SIGINT interrupt
def signal_handler(signum, frame):
    global keep_running
    keep_running    = False

def loop(   loglevel    = 1,
            avg_sec     = 30):
    global keep_running

    #setting up GPS buffer
    GPS_data        = []
    sensor_data     = []
    counter         = 0

    #Do some stuff while motion is not detected and wait
    #start   = dt.now()
    #while dt.now()-start < tidt(seconds=30.):
    while keep_running:
        #Handle GPS data once every second
        c_ti    = time.time()
        if c_ti - l_data_ti >= 1.:
            if loglevel == 0:
                print("counter={}".format(counter))
            GPS_point       = format_gps_data()
            #Speed in km/h
            speed[counter]  = float(GPS_point[3])*3.6
            if np.isnan(speed[counter]):
                speed[counter] = 0.0
            spee        = np.mean(speed)
            if loglevel == 0:
                print("speed={}".format(spee))

            out = ""
            for da in GPS_point:
                out += "{}\t".format(da)

            out += "{}".format(spee)

            if loglevel == 0:
                print(out)
            with open("/tmp/gps.data","w") as fi:
                fi.write(out)

            l_data_ti   = c_ti
            counter    += 1
            counter    %= int(avg_sec)
        time.sleep(0.2)

if __name__ == "__main__":
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = OptionParser()

    parser.add_option(  "-f", "--praefix", dest="praefix",default="",
                        help="File praefix and folder localtion")
    parser.add_option(  "", "--postfix", dest="postfix",
                        default="",
                        help="Specify custom input file postfix")
    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")

    (options, args) = parser.parse_args()

    loop(  loglevel=int(options.loglevel))
