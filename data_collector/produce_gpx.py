import numpy as np
import h5py 
import matplotlib as mt
import matplotlib.pyplot as plt
import datetime as dt
from optparse import OptionParser
import gpxpy
import gpxpy.gpx

def ti_to_dt(ti):
    return dt.datetime(2000,1,1)+dt.timedelta(seconds=ti)

def ti_to_dt_str(ti):
    dti     = dt.datetime(2000,1,1)+dt.timedelta(seconds=ti)
    return dt.datetime.strftime(dti,"%H:%M:%S %d.%m.%Y")

def output_gpx(f):
    d_GPS   = f["/GPS"]
    print(d_GPS[0])
    dtis    = [ti_to_dt(igps[0]) for igps in d_GPS[:,:]]
    dtis    = np.array(dtis)

    gpx = gpxpy.gpx.GPX()

    # Create first track in our GPX:
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)

    # Create first segment in our GPX track:
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for i in range(len(dtis)):
        gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(  d_GPS[i,1],
                                                            d_GPS[i,2],
                                                            speed=d_GPS[i,3]*3.6,
                                                            time=dtis[i]))

    return gpx

if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option(  "-f", "--file", dest="file",default="demo.hdf5",
                        help="Specify input file name")

    (options, args) = parser.parse_args()
    f           = h5py.File(options.file,"r",swmr=True)
    gpx_obj     = output_gpx(f)
    f.close()
    with open("{}.gpx".format(options.file[:-5]), "w") as f:
        f.write( gpx_obj.to_xml())
