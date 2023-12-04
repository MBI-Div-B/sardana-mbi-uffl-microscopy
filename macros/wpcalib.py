import numpy as np
import lmfit

from sardana.macroserver.macro import imacro, Type, Optional
from sardana.macroserver.scan import *


@imacro([["counter", Type.ExpChannel, Optional, "pm_pump"]])
def wpCalibScan(self, counter):
    """This runs a waveplate calibration scan"""

    acqConf = self.getEnv("acqConf")
    oldWaitTime = acqConf["waitTime"]
    newWaitTime = 1

    if counter is None:
        counter = "pm_pump"

    self.output("User counter %s for waveplate calibration scan.", counter)
    motor = "wp"

    self.execMacro("plotselect", counter)

    self.execMacro("waittime", newWaitTime)
    # self.execMacro('altoff')
    # self.execMacro('pumpoff')

    scan, _ = self.createMacro("ascan", "wp", "-5", "55", "60", "1")
    # createMacro returns a tuple composed from a macro object
    # and the result of the Macro.prepare method

    self.runMacro(scan)

    self.execMacro("waittime", oldWaitTime)

    data = scan.data

    wp = []
    pm = []

    for idx, rc in data.items():
        pm.append(rc[counter])
        wp.append(rc[motor])

    pm = np.array(pm)
    wp = np.array(wp)
    # remove nans
    wp = wp[np.logical_not(np.isnan(pm))]
    pm = pm[np.logical_not(np.isnan(pm))]

    mod = lmfit.Model(sinSqrd)
    par = lmfit.Parameters()

    par.add("Pm", value=0.5, vary=True, min=0)
    par.add("P0", value=0, vary=True)
    par.add("offset", value=0, vary=True)
    par.add("period", value=1, vary=True, min=0.9, max=1.1)

    out = mod.fit(pm, par, x=wp)

    self.info(out.best_values)

    self.pyplot.plot(wp, pm, "o", label="data")
    self.pyplot.plot(wp, out.best_fit, label="fit")
    self.pyplot.title(
        r"Fit data by $P(wp) = P_m*(sin((wp-offset)*2/180*\pi*period)^2)+P_0$"
    )
    self.pyplot.xlabel("wp angle [deg.]")
    self.pyplot.xlabel("laser power [W]")
    self.pyplot.legend()

    self.execMacro(
        "powerconf",
        out.best_values["P0"],
        out.best_values["Pm"],
        out.best_values["offset"],
        out.best_values["period"],
    )


def sinSqrd(x, Pm, P0, offset, period):
    return Pm * (np.sin(np.radians(x - offset) * 2 * period) ** 2) + P0
