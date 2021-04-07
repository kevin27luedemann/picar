import numpy as np
from picamera import PiCamera
from picamera import array
from picamera import PiCameraCircularIO as circular
import time
import datetime as dt
import h5py

class hdf5_storage(array.PiYUVAnalysis):
    def __init__(self,camera,dset,h5file):
        super(hdf5_storage, self).__init__(camera)
        self.dset       = dset
        self.h5file     = h5file
    
    def analyse(self,a):
        self.dset.resize(self.dset.len()+1,axis=0)
        self.dset[self.dset.len()-1]    = a[:,:,0]

def main():
    f                   = h5py.File("demo.hdf5","w",driver="stdio",libver="latest")
    f.swmr_mode         = True
    
    camera              = PiCamera()
    camera.resolution   = (1920,1080)
    camera.framerate    = 10

    #start warm up befor recording to get exposure right
    camera.start_preview()
    time.sleep(2)
    dummy               = array.PiYUVArray(camera)
    camera.capture(dummy,use_video_port=True,format="yuv")
    dset                = f.create_dataset( "sequence",
                                            data=[dummy.array[:,:,0]],
                                            maxshape=(  None,
                                                        dummy.array.shape[0],
                                                        dummy.array.shape[1]),
                                            chunks=True)

    #setup circular io buffer
    stream              = circular(camera, seconds=10)
    h5_writer           = hdf5_storage(camera,dset,f)
    
    #start actual recording
    camera.start_recording(stream, format="h264")
    camera.wait_recording(10)
    camera.start_recording(h5_writer, format="yuv", splitter_port=2)
    camera.wait_recording(10)

    #stop all the recording
    camera.stop_recording(splitter_port=2)
    camera.stop_recording()

    #save the ring buffer to file
    stream.copy_to("my_stream.mp4",seconds=10)
    camera.stop_preview()

    #close the HDF5 file
    f.close()

if __name__ == "__main__":
    main()
