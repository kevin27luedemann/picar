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

def loop(   prefix      = "",
            loglevel    = 1):
    global keep_running

    #setting up GPS buffer
    GPS_data        = []
    sensor_data     = []
    counter         = 0

    while keep_running:
        #Handle GPS data once every second
        c_ti    = time.time()
        if c_ti - l_data_ti >= 1.:
            GPS_data    = np.genfromtxt("/tmp/gps.data")
            sensor_data = np.genfromtxt("/tmp/sensors.data")
            if loglevel == 0:
                print(GPS_data)
                print(sensor_data)
            out_data = ""
            for da in GPS_data:
                out_data    += "{}\t".format(da)

            for da in sensor_data[:-1]:
                out_data    += "{}\t".format(da)
            out_data        += "{}\n".format(sensor_data[-1])
            #combine all data and write to file
            fname       = dt.datetime.strftime(dt.now(),"%Y%m%d.txt")
            fname       = os.path.join(prefix,fname)
            with open(fname,"a") as output:
                output.write(out_data)
        time.sleep(0.2)

if __name__ == "__main__":
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    parser = OptionParser()

    parser.add_option(  "-f", "--prefix", dest="prefix",default="./",
                        help="File prefix and folder localtion")
    parser.add_option(  "", "--postfix", dest="postfix",
                        default="",
                        help="Specify custom input file postfix")
    parser.add_option(  "-v", "--loglevel", dest="loglevel",default=1,
                        help="Loglevel: 0:verbose, 1:moderate, 2:quiet")

    (options, args) = parser.parse_args()

    loop(  prefix=options.prefix,
            loglevel=int(options.loglevel))
