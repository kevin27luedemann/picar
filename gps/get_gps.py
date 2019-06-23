#!/usr/bin/env python3
import gpsd

# Connect to the local gpsd
gpsd.connect()

# Get gps position
packet = gpsd.get_current()

if packet.mode >= 2:
    print("  Latitude: " + str(packet.lat))
    print(" Longitude: " + str(packet.lon))
    print(" Track: " + str(packet.track))
    print("  Horizontal Speed: " + str(packet.hspeed))
    print(" Time: " + str(packet.time))
    print(" Error: " + str(packet.error))

if packet.mode >= 3:
    print("  Altitude: " + str(packet.alt))
    print(" Climb: " + str(packet.climb))

print(" ************** METHODS ************** ")
if packet.mode >= 2:
    print("  Location: " + str(packet.position()))
    print(" Speed: " + str(packet.speed()))
    print("Position Precision: " + str(packet.position_precision()))
    print("   Map URL: " + str(packet.map_url()))

if packet.mode >= 3:
    print("  Altitude: " + str(packet.altitude()))
    print("  Movement: " + str(packet.movement()))
    print("  Speed Vertical: " + str(packet.speed_vertical()))

print(" ************* FUNCTIONS ************* ")
print("Device: " + str(gpsd.device()))
