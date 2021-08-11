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

def init_gps():
    # Connect to the local gpsd
    gpsd.connect()
    #dummy read which is needed at the beginning for some reason
    collect_gps_data()

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

def format_gps_data(blocking=False):
    ti,da,er    = collect_gps_data()
    if ti == '' and blocking:
        while ti == '':
            time.sleep(0.01)
            ti,da,er    = collect_gps_data()
        dti     = dt.datetime.strptime(ti,"%Y-%m-%dT%H:%M:%S.%fZ")
    else:
        dti     = dt.datetime.now()
    ti_sec      = dt.datetime.strftime(dti,"%Y%m%d%H%M%S")
    GPS_point   = np.append(da,er,axis=0)
    GPS_point   = np.append(np.array([ti_sec]),GPS_point,axis=0)
    return GPS_point

def loop(   loglevel    = 1,
            avg_sec     = 30):
    global keep_running

    #setting up GPS buffer
    l_data_ti       = 0.
    GPS_point       = format_gps_data()
    speed           = np.ones(30)
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

    init_gps()

    loop(  loglevel=int(options.loglevel))
