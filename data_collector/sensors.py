#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", message="PiCameraResolutionRounded")
import numpy as np
import h5py
import time
import signal,os,sys
import datetime as dt
from datetime import timedelta as tidt
from io import BytesIO
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

def loop(   sensor,
            loglevel=1):
    global keep_running

    #setting up GPS buffer
    l_data_ti       = 0.

    #Do some stuff while motion is not detected and wait
    #start   = dt.now()
    #while dt.now()-start < tidt(seconds=30.):
    while keep_running:
        #Handle GPS data once every second
        c_ti    = time.time()
        if c_ti - l_data_ti >= 1.:
            sensor.icm20948_Gyro_Accel_Read()
            gs      = np.copy(sense.Accel)/16384
            
            dti     = dt.datetime.now()
            ti_sec  = dt.datetime.strftime(dti,"%Y%m%d%H%M%S")

            out     = ""
            out     += "{}\t".format(ti_sec)
            for g in gs:
                out += "{}\t".format(g)

            if loglevel == 0:
                print(out)
            with open("/tmp/sensors.data","w") as fi:
                fi.write(out)

            l_data_ti   = c_ti

        time.sleep(0.2)

if __name__ == "__main__":
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = OptionParser()

    parser.add_option(  "-f", "--praefix", dest="praefix",default="",
                        help="File praefix and folder localtion")
    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")

    (options, args) = parser.parse_args()

    if options.loglevel == 0:
        print(fname)

    sensor              = sense.ICM20948()

    loop(   sensor,
            loglevel=int(options.loglevel))
