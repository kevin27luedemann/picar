import sys,os
import obd
import datetime as dt
import time
from pprint import pprint
import json
import signal

cmds = ["SPEED",
        "RPM",
        "ENGINE_LOAD",
        "THROTTLE_POS",
        "FUEL_LEVEL",
        "COOLANT_TEMP",
        "DISTANCE_W_MIL"
        ]

interupt_flag   = True
def signal_handler(sig, frame):
    global interupt_flag
    interupt_flag = False
signal.signal(signal.SIGINT, signal_handler)
    
def main():
    global interupt_flag
    save    = True
    con     = obd.OBD("/dev/serial0",115200)
    print(con.status())
    counter = 0
    data    = {}
    while(interupt_flag):
        status = {}
        for cmd in sorted(cmds):
            status.update({cmd:str(con.query(obd.commands[cmd],force=True).value)})
        now   = dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S")
        data.update({now:status})
        pprint(status)
        time.sleep(2)
        counter = counter + 1
        if counter >= 600:
            if save:
                with open(now+".dat","w+") as dafi:
                    json.dump(data,dafi,sort_keys=True,indent=4)
            data    = {}
            counter = 0

    if save:
        now   = dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S")
        with open(now+".dat","w+") as dafi:
            json.dump(data,dafi,sort_keys=True,indent=4)
    con.close()

if __name__ == "__main__":
    main()
