import numpy as np
import h5py 
import matplotlib as mt
import matplotlib.pyplot as plt
import animation as an
import datetime as dt
from optparse import OptionParser

def ti_to_dt(ti):
    return dt.datetime(2000,1,1)+dt.timedelta(seconds=ti)

def ti_to_dt_str(ti):
    dti     = dt.datetime(2000,1,1)+dt.timedelta(seconds=ti)
    return dt.datetime.strftime(dti,"%H:%M:%S %d.%m.%Y")

def animate_timelaps(f,fps=2):
    d_pic       = f["/timelaps"]
    d_pti       = f["/timelaps_ti"]
    it,dy,dx    = d_pic.shape

    title       = [ti_to_dt_str(ti[0]) for ti in d_pti[:]]

    ani = an.anim.anim( [d_pic],
                        title,
                        num_axis=1,
                        max_count=it)
    ani.set_FPS(fps)
    im          = ani.ax.imshow(d_pic[0,:,:],cmap="gray")
    ani.ax.axis(False)

    def update(ax,li,data,title,num):
        li[0].set_array(data[0][num,:,:])
        ax.draw_artist(li[0])
        ax.set_title(title)

    ani.animate([im],update)
    plt.show()

def show_gps_time_data(f):
    d_GPS   = f["/GPS"]
    print(d_GPS[0])
    dtis    = [ti_to_dt(igps[0]) for igps in d_GPS[:,:]]
    dtis    = np.array(dtis)

    #fig,ax  = plt.subplots(3,sharex=True)
    #Ther is something wrong with the erorr form GPSD
    #ax[0].errorbar(dtis,d_GPS[:,1],yerr=d_GPS[:,8])
    #ax[1].errorbar(dtis,d_GPS[:,2],yerr=d_GPS[:,9])
    #ax[2].errorbar(dtis,d_GPS[:,3],yerr=d_GPS[:,10])
    #ax[0].plot(dtis,d_GPS[:,1],"r+-")
    #ax[1].plot(dtis,d_GPS[:,2],"r+-")
    #ax[0].set_ylabel("Latitude")
    #ax[1].set_ylabel("Longitude")
    fig,ax  = plt.subplots()

    ax.plot(dtis,d_GPS[:,3]*3.6,"r+-")
    ax.set_ylabel("Speed/ km h^-1")

    fig.autofmt_xdate()

    #Plot horizontal position
    fig2,ax2= plt.subplots()
    ax2.plot(d_GPS[:,1],d_GPS[:,2],"r+-")
    ax2.set_xlabel("Latitude")
    ax2.set_ylabel("Longitude")

    plt.show()

if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option(  "-f", "--file", dest="file",default="demo.hdf5",
                        help="Specify input file name")

    parser.add_option(  "-a", "--animate", dest="animate",
                        action="store_true",default=False,
                        help="Specify input file name")

    (options, args) = parser.parse_args()
    f           = h5py.File(options.file,"r",swmr=True)
    if options.animate:
        animate_timelaps(f)
    show_gps_time_data(f)
    f.close()
