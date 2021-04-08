import numpy as np
import h5py 
import matplotlib as mt
import matplotlib.pyplot as plt
import animation as an
import datetime as dt

def ti_to_dt(ti):
    return dt.datetime(2000,1,1)+ti
    

def animate_timelaps(f):
    d_pic       = f["/timelaps"]
    d_pti       = f["/timelaps_ti"]
    print(d_pic.shape)
    print(d_pti.shape)
    it,dy,dx    = dset.shape

    ani = an.anim.anim( [dset],
                        ["{}".format(ti_to_dt(ti)) for ti in d_pti[:]],
                        num_axis=1,
                        max_count=it)
    ani.set_FPS(10)
    im          = ani.ax.imshow(dset[0,:,:],cmap="gray")
    ani.ax.axis(False)

    def update(ax,li,data,title,num):
        li[0].set_array(data[0][num,:,:])
        ax.draw_artist(li[0])
        ax.set_title(title)

    ani.animate([im],update)
    plt.show()

if __name__ == "__main__":
    f           = h5py.File("./demo.hdf5","r",swmr=True)
    animate_timelaps()
    f.close()
