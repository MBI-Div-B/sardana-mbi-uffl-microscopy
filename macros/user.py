from sardana.macroserver.macro import Macro, macro, Type
from time import sleep
from tango import DeviceProxy

from dirsync import sync
import os
import subprocess


@macro()
def user_pre_acq(self):
    """Macro user_pre_acq"""
    acqConf = self.getEnv("acqConf")

    try:
        waittime = acqConf["waitTime"]
    except:
        self.warning("env variable acqConf/waitTime not found!")
        waittime = 0
    if waittime > 0:
        sleep(waittime)
        self.debug("waiting for %.2f s", waittime)


@macro()
def user_pre_scan(self):
    """Macro user_pre_scan"""
    acqConf = self.getEnv("acqConf")

    self.execMacro("acqrep")


@macro()
def user_post_scan(self):
    """Macro user_pre_scan"""
    acqConf = self.getEnv("acqConf")


@macro()
def user_post_scan_sync(self):
    scanDir = self.getEnv("ScanDir")

    #    sync_cmd = ["sshpass", "-p", "'cV4mBBpS2StpqBP'", "rsync", "-r", "-t", "-g", "-v", "--progress", "-s", "/home/labuser/data", "data_ampere@nasbsxr.sxr.lab:/share/Data/ampere.sxr.lab/RSXS"]

    if scanDir is not "" and scanDir is not None:
        self.output("Mirroring on NAS initiated...")
        result = subprocess.run(
            f'rsync -r -t -g -v --progress -s --include="*_[0-9][0-9][0-9][0-9].h5" --exclude="*.h5" {scanDir} data_ampere@nasbsxr.sxr.lab:/share/Data/henry.sxr.lab/RSXS/data',
            shell=True,
            stdout=subprocess.PIPE,
        )
        self.output(result.stdout.decode("utf-8"))
        self.output("End of mirroring.")
    else:
        self.output("ScanDir is not set, please check the save path.")
