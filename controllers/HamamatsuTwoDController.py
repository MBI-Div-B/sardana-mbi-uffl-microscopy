from tango import DeviceProxy
from PIL import Image
import numpy
import time
from sardana.pool.controller import TwoDController, Referable, Type, Description, DefaultValue, FGet, FSet
from sardana import State

class HamamatsuTwoDController(TwoDController, Referable):
    """The most basic controller intended from demonstration purposes only.
    This is the absolute minimum you have to implement to set a proper counter
    controller able to get a counter value, get a counter state and do an
    acquisition.

    This example is so basic that it is not even directly described in the
    documentation"""
    ctrl_properties = {'tangoFQDN': {Type: str, 
                              Description: 'The FQDN of the greateyes tango DS', 
                              DefaultValue: 'greateyes.hhg.lab'},
                       }

    axis_attributes = {
             "SavingEnabled": {
                Type: bool,
                FGet: "isSavingEnabled",
                FSet: "setSavingEnabled",
                Description: ("Enable/disable saving of images in HDF5 files."
                              " Use with care in high demanding (fast)"
                              " acquisitions. Trying to save at high rate may"
                              " hang the acquisition process."),
             }
        }

    def AddDevice(self, axis):
        self._axes[axis] = {}

    def DeleteDevice(self, axis):
        self._axes.pop(axis)

    def __init__(self, inst, props, *args, **kwargs):
        """Constructor"""
        TwoDController.__init__(self,inst,props, *args, **kwargs)
        print ('GreatEyes Tango Initialization ...')
        self.proxy = DeviceProxy(self.tangoFQDN)
        print ('SUCCESS')
        self._axes = {}
        
    def ReadOne(self, axis):
        """Get the specified counter value"""    
        im = self.proxy.last_image
        image = Image.frombytes("L", (self.proxy.image_width, self.proxy.image_height), im[1])
        return numpy.array(image)
    
    def RefOne(self, axis):
        pass
    
    def SetAxisPar(self, axis, parameter, value):
#        if parameter == "value_ref_pattern":
#            print('value_ref_pattern ' + str(value))
#        elif parameter == "value_ref_enabled":
#            print('value_ref_enabled ' + str(value))
#            self.setSavingEnabled(axis, value)
        pass

    def StateOne(self, axis):
        """Get the specified counter state"""
        if self.proxy.acq_status == 'Running':
            return State.Moving
        else:
            return State.On

    def PrepareOne(self, axis, value, repetitions, latency, nb_starts):
        self.proxy.acq_nb_frames = 1
        self.proxy.acq_expo_time = value
    
    def LoadOne(self, axis, value, repetitions, latency):
        pass

    def PreStartOne(self, axis, value):
        self.proxy.prepareAcq()
        return True

    def StartOne(self, axis, value):
        """acquire the specified counter"""
        self.proxy.startAcq()
        # wait to avoid too fast status read-backs
        time.sleep(0.1)

    def StopOne(self, axis):
        """Stop the specified counter"""
        self.proxy.stopAcq()
    
    def AbortOne(self, axis):
        """Abort the specified counter"""
        pass

    def GetAxisPar(self, axis, par):
        if par == "shape":
            return [self.proxy.image_width, self.proxy.image_height]
