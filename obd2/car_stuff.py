import sys,os
sys.path.append("/home/pi/Documents/python-OBD/")
import obd
import datetime as dt
import time

def get_speed(con):
    cmd     = obd.commands.SPEED
    resp    = con.query(cmd)
    return resp.value

def get_RPM(con):
    cmd     = obd.commands.RPM
    resp    = con.query(cmd)
    return resp.value

def get_FUEL_STATUS(con):
    cmd     = obd.commands.FUEL_STATUS
    resp    = con.query(cmd)
    return resp.value
    
def get_ENGINE_LOAD(con):
    cmd     = obd.commands.ENGINE_LOAD
    resp    = con.query(cmd)
    return resp.value

def get_COOLANT_TEMP(con):
    cmd     = obd.commands.COOLANT_TEMP
    resp    = con.query(cmd)
    return resp.value

def get_THROTTLE_POS(con):
    cmd     = obd.commands.THROTTLE_POS
    resp    = con.query(cmd)
    return resp.value

def get_DISTANCE_W_MIL(con):
    cmd     = obd.commands.DISTANCE_W_MIL
    resp    = con.query(cmd)
    return resp.value

def get_FUEL_LEVEL(con):
    cmd     = obd.commands.FUEL_LEVEL
    resp    = con.query(cmd)
    return resp.value

def get_DISTANCE_SINCE_DTC_CLEAR(con):
    cmd     = obd.commands.DISTANCE_SINCE_DTC_CLEAR
    resp    = con.query(cmd)
    return resp.value

def get_FUEL_RATE(con):
    cmd     = obd.commands.FUEL_RATE
    resp    = con.query(cmd)
    return resp.value

def get_OIL_TEMP(con):
    cmd     = obd.commands.OIL_TEMP
    resp    = con.query(cmd)
    return resp.value

def get_ELM_VOLTAGE(con):
    cmd     = obd.commands.ELM_VOLTAGE
    resp    = con.query(cmd)
    return resp.value
    
def main():
    con = obd.OBD("/dev/serial0",115200)
    now         = dt.datetime.now()
    file_name   = dt.datetime.strftime(now,"%Y%m%d_%H%M%S.dat")
    print(file_name)
    dafi    = open(file_name,"w+")
    counter = 0
    while(counter < 2):
        #status = "200"
        status = []
        status.append(con.status())
        status.append(get_speed(con))
        status.append(get_RPM(con))
        status.append(get_FUEL_STATUS(con))
        status.append(get_ENGINE_LOAD(con))
        status.append(get_COOLANT_TEMP(con))
        status.append(get_THROTTLE_POS(con))
        status.append(get_DISTANCE_W_MIL(con))
        status.append(get_FUEL_LEVEL(con))
        status.append(get_DISTANCE_SINCE_DTC_CLEAR(con))
        status.append(get_FUEL_RATE(con))
        status.append(get_OIL_TEMP(con))
        status.append(get_ELM_VOLTAGE(con))
        print(status)
        dafi.write("".join(status))
        time.sleep(1)
        counter = counter + 1

    dafi.close()



if __name__ == "__main__":
    main()
