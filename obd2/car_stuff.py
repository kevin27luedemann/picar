import sys,os
import obd
import datetime as dt
import time

cmds = [obd.commands.SPEED,
        obd.commands.RPM,
        obd.commands.ENGINE_LOAD,
        obd.commands.THROTTLE_POS,
        obd.commands.FUEL_LEVEL,
        obd.commands.FUEL_RATE,
        #obd.commands.FUEL_STATUS,
        obd.commands.COOLANT_TEMP,
        obd.commands.DISTANCE_W_MIL,
        obd.commands.DISTANCE_SINCE_DTC_CLEAR,
        obd.commands.OIL_TEMP
       # obd.commands.ELM_VOLTAGE
        ]
    
def main():
    con = obd.OBD("/dev/serial0",115200)
    print(con.status())
    now         = dt.datetime.now()
    file_name   = dt.datetime.strftime(now,"%Y%m%d_%H%M%S.dat")
    print(file_name)
    #dafi    = open(file_name,"w+")
    counter = 0
    while(counter < 2):
        status = []
        for cmd in cmds:
            status.append(con.query(cmd).value)
        print(status)
        #dafi.write("".join(status))
        time.sleep(1)
        counter = counter + 1

    #dafi.close()



if __name__ == "__main__":
    main()
