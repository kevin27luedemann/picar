#!/usr/bin/env python3
import gpsd
import numpy as np
import h5py
import time
import datetime as dt

def init_gps():
    # Connect to the local gpsd
    gpsd.connect()
    #dummy read which is needed at the beginning for some reason
    collect_data()

def collect_data():
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

if __name__ == "__main__":
    init_gps()

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
