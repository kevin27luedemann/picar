import numpy as np
import shutil
import time
import signal,os,sys
import datetime as dt
from glob import glob

keep_running        = True

def signal_handler(signum, frame):
    global keep_running
    keep_running    = False

def get_usage(name="/"):
    total, used, free   = shutil.disk_usage(name)
    free_percent        = free/total
    used_percent        = used/total
    return free_percent,used_percent

def loop(folder="/videos/",mount="/",dt=20,loglevel=2):
    while(keep_running):
        fpercent,upercent           = get_usage(name=mount)
        if loglevel <= 1:
            print(upercent)
        if upercent >= 0.85:
            fnames                  = glob(os.path.join(folder,"*.mp4"))
            fnames.sort(key=lambda x: os.path.getmtime(x))
            if loglevel == 0:
                print(upercent)
            while upercent > 0.75:
                if loglevel == 0:
                    print(fnames[0])
                os.remove(fnames[0])
                fpercent,upercent   = get_usage(name=mount)
                fnames              = glob(os.path.join(folder,"*.mp4"))
                fnames.sort(key=lambda x: os.path.getmtime(x))
        time.sleep(dt)

if __name__ == "__main__":
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    loop()
