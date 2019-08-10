import sys,os
import obd
import datetime as dt
import time
from pprint import pprint
import json
import signal
from optparse import OptionParser

interupt_flag   = True
def signal_handler(sig, frame):
    global interupt_flag
    interupt_flag = False
signal.signal(signal.SIGINT, signal_handler)
    
def main():
    global interupt_flag
    parser = OptionParser()
    #parser.add_option("-f", "--file", dest="filename",
    #                  help="write report to FILE", metavar="FILE")
    parser.add_option("-s", "--save",
                      action="store_true", dest="save", default=False,
                      help="Save data to file")
    parser.add_option("-q", "--quiet",
                      action="store_true", dest="quiet", default=False,
                      help="don't print anything")
    parser.add_option("", "--debug",
                      action="store_true", dest="debug", default=False,
                      help="print debug output")
    parser.add_option("", "--noloop",
                      action="store_true", dest="noloop", default=False,
                      help="do not loop, only run once")


    (options, args) = parser.parse_args()

    con     = obd.OBD("/dev/serial0",115200,fast=False)
    if options.debug:
        obd.logger.setLevel(obd.logging.DEBUG)
    if not(options.quiet):
        print(con.status())
    cmdsup  = con.supported_commands
    cmds    = []
    for cmd in cmdsup:
        if  not("DTC" in cmd.name) and \
            not("MONITOR" in cmd.name) and \
            not("PID" in cmd.name) and \
            not("VERSION" in cmd.name) and \
            not("OBD" in cmd.name) and \
            not("STATUS" in cmd.name) and \
            not("MID" in cmd.name) and \
            not("O2_SENSORS" in cmd.name):
            cmds.append(cmd.name)
    counter = 0
    data    = {}
    while(interupt_flag):
        if options.noloop:
            interupt_flag = False
        status = {}
        for cmd in sorted(cmds):
            status.update({cmd:str(con.query(obd.commands[cmd]).value)})
        now   = dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S")
        data.update({now:status})
        if not(options.quiet):
            pprint(status)
        time.sleep(2)
        counter = counter + 1
        if counter >= 600:
            if options.save:
                with open(now+".dat","a") as dafi:
                    json.dump(data,dafi,sort_keys=True,indent=4)
            data    = {}
            counter = 0

    if options.save:
        now   = dt.datetime.strftime(dt.datetime.now(),"%Y%m%d_%H%M%S")
        with open(now+".dat","w+") as dafi:
            json.dump(data,dafi,sort_keys=True,indent=4)
    con.close()

if __name__ == "__main__":
    main()
