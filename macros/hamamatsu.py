from sardana.macroserver.macro import Macro, macro, imacro, Type
from time import sleep
from tango import DeviceProxy

HAMAMATSU_DS = 'lima/limaccd/1'


def get_proxy(macro_obj):
    try:
        proxy = DeviceProxy(HAMAMATSU_DS)
    except Exception:
        raise ValueError('Could not open proxy to {:s}'.format(HAMAMATSU_DS))
    return proxy


@macro(
    [
        ["exp_time", Type.Float, 1, "exposure time [s]"],
    ]
)
def hamamatsu_continuous_acq(self, exp_time):
    ds = get_proxy(self)
    ds.stopAcq()
    ds.acq_expo_time = exp_time
    ds.acq_nb_frames = 0
    ds.prepareAcq()
    ds.startAcq()
    self.output("started continuous acquistion with {:f} s integration time".format(exp_time))


@macro()
def hamamatsu_stop_acq(self):
    ds = get_proxy(self)
    ds.stopAcq()
    self.output("stopped acquisition")


@macro([["output", Type.Boolean, True, "enable output"],])
def hamamatsu_get_image_size(self, output=True):
    """Macro to get image size of hamamatus camera"""
    ds = get_proxy(self)
    sizes = ds.image_sizes
    if output:
        self.output("width X: {: >4d} px".format(sizes[2]))
        self.output("width Y: {: >4d} px".format(sizes[3]))
    return sizes[2:3]


@macro([["output", Type.Boolean, True, "enable output"],])
def hamamatsu_get_image_max_dims(self, output=True):
    """Macro to get image max dimensions of hamamatus camera"""
    ds = get_proxy(self)
    max_dims = ds.image_max_dim
    if output:
        self.output("max width X: {: >4d} px".format(max_dims[0]))
        self.output("max width Y: {: >4d} px".format(max_dims[1]))
    return max_dims


@macro([["output", Type.Boolean, True, "enable output"],])
def hamamatsu_get_roi(self, output=True):
    """Macro to get ROI parameters of hamamatus camera"""
    ds = get_proxy(self)
    roi = ds.image_roi
    if output:
        self.output("start X: {: >4d} px".format(roi[0]))
        self.output("start Y: {: >4d} px".format(roi[1]))
        self.output("width X: {: >4d} px".format(roi[2]))
        self.output("width Y: {: >4d} px".format(roi[3]))
    return roi


@macro(
    [
        ["start_x", Type.Integer, None, "start x"],
        ["start_y", Type.Integer, None, "start y"],
        ["width_x", Type.Integer, None, "width x"],
        ["width_y", Type.Integer, None, "width y"],
    ]
)
def hamamatsu_set_roi(self, start_x, start_y, width_x, width_y):
    """Macro to set ROI parameters of hamamatus camera"""
    import numpy as np
    ds = get_proxy(self)
    (bin_x, bin_y) = self.runMacro("hamamatsu_get_binning", "False")
    (max_size_x, max_size_y) = self.runMacro("hamamatsu_get_image_max_dims", "False")
    if start_x < 0 or start_y < 0 or width_x < 0 or width_y < 0:
        self.error("all input parameters must positive integers!")
        return
    if (start_x + width_x) > max_size_x/bin_x:
        self.error("sum of `start_x` and `width_x` exceed max. possible value of {:d} px!".format(int(np.floor(max_size_x/bin_x))))
        return
    if (start_y + width_y) > max_size_y/bin_y:
        self.error("sum of `start_x` and `width_x` exceed max. possible value of {:d} px!".format(int(np.floor(max_size_x/bin_x))))
        return
    ds.image_roi = [start_x, start_y, width_x, width_y]
    self.output("image roi set to:")
    self.execMacro("hamamatsu_get_roi")


@macro([["output", Type.Boolean, True, "enable output"],])
def hamamatsu_get_binning(self, output=True):
    """Macro to get binning parameters of hamamatus camera"""
    ds = get_proxy(self)
    bins = ds.image_bin
    if output:
        self.output("binning X: {: >2d}".format(bins[0]))
        self.output("binning Y: {: >2d}".format(bins[1]))
    return bins


@macro(
    [
        ["bin_x", Type.Integer, 1, "binning x"],
        ["bin_y", Type.Integer, 1, "binning y"],
    ]
)
def hamamatsu_set_binning(self, bin_x, bin_y):
    """Macro to set binning parameters of hamamatus camera"""
    ds = get_proxy(self)
    ds.image_bin = [bin_x, bin_y]
    self.output("binning set to:")
    self.execMacro("hamamatsu_get_binning")

