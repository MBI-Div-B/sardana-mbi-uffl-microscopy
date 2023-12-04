from sardana.macroserver.macro import imacro, macro, Type, Optional
from tango import DeviceProxy
import numpy as np


@imacro(
    [
        ["waitTime", Type.Float, Optional, "wait time"],
    ]
)
def acqconf(
    self,
    waitTime,
):
    # run all the other configurations
    try:
        acqConf = self.getEnv("acqConf")
    except:
        acqConf = {}

    self.setEnv("acqConf", acqConf)

    self.execMacro("waittime", waitTime)

    self.execMacro('powerconf')
    self.execMacro('fluenceconf')
    self.output('\r')
    self.execMacro('acqrep')


@macro()
def acqrep(self):
    acqConf = self.getEnv("acqConf")
    self.output(
        "Gen. Settings:\nWaittime = %.2f s",
        acqConf["waitTime"],
    )
    self.execMacro("powerrep")
    self.execMacro("fluencerep")


@imacro([["time", Type.Float, Optional, "time in seconds"]])
def waittime(self, time):
    """Macro waittime"""
    acqConf = self.getEnv("acqConf")

    if time is None:
        label, unit = "Waittime", "s"
        time = self.input(
            "Wait time before every acqisition?",
            data_type=Type.Float,
            title="Waittime Amplitude",
            key=label,
            unit=unit,
            default_value=acqConf["waitTime"],
            minimum=0.0,
            maximum=100,
        )

    acqConf["waitTime"] = time
    self.setEnv("acqConf", acqConf)
    self.output("waittime set to %.2f s", time)


@imacro(
    [
        ["pumpHor", Type.Float, Optional, "pumpHor"],
        ["pumpVer", Type.Float, Optional, "pumpVer"],
        ["refl", Type.Float, Optional, "reflectivity"],
        ["repRate", Type.Float, Optional, "repetition rate"],
    ]
)
def fluenceconf(self, pumpHor, pumpVer, refl, repRate):
    fluencePM = DeviceProxy("pm/fluencectrl/1")
    try:
        lastPumpHor = fluencePM.pumpHor
        lastPumpVer = fluencePM.pumpVer
        lastRefl = fluencePM.refl
        lastRepRate = fluencePM.repRate
    except:
        lastPumpHor = 100
        lastPumpVer = 100
        lastRefl = 0
        lastRepRate = 3000

    if pumpHor is None:
        label, unit = "hor", "um"
        pumpHor = self.input(
            "Set the horizontal beam diameter (FWHM):",
            data_type=Type.Float,
            title="Horizontal beam diameter",
            key=label,
            unit=unit,
            default_value=lastPumpHor,
            minimum=0.0,
            maximum=100000,
        )
    if pumpVer is None:
        label, unit = "ver", "um"
        pumpVer = self.input(
            "Set the vertical beam diameter (FWHM):",
            data_type=Type.Float,
            title="Vertical beam diameter",
            key=label,
            unit=unit,
            default_value=lastPumpVer,
            minimum=0.0,
            maximum=100000,
        )
    if refl is None:
        label, unit = "refl", "%"
        refl = self.input(
            "Set the sample reflectivity:",
            data_type=Type.Float,
            title="Sample reflectivity",
            key=label,
            unit=unit,
            default_value=lastRefl,
            minimum=0.0,
            maximum=100,
        )
    if repRate is None:
        label, unit = "repRate", "Hz"
        repRate = self.input(
            "Set the laser repetition rate:",
            data_type=Type.Float,
            title="Laser repetition rate",
            key=label,
            unit=unit,
            default_value=lastRepRate,
            minimum=0.0,
            maximum=100000,
        )

    fluencePM.pumpHor = pumpHor
    fluencePM.pumpVer = pumpVer
    fluencePM.refl = refl
    fluencePM.repRate = repRate

    power = self.getPseudoMotor("power")
    fluence = self.getPseudoMotor("fluence")
    minPower, maxPower = power.getPositionObj().getLimits()

    trans = 1 - (refl / 100)
    minFluence = (
        minPower
        * trans
        / (repRate / 1000 * np.pi * pumpHor / 10000 / 2 * pumpVer / 10000 / 2)
    )
    maxFluence = (
        maxPower
        * trans
        / (repRate / 1000 * np.pi * pumpHor / 10000 / 2 * pumpVer / 10000 / 2)
    )
    self.info("Update limits of pseudo motor fluence")
    fluence.getPositionObj().setLimits(minFluence, maxFluence)

    self.execMacro("fluencerep")


@macro()
def fluencerep(self):
    fluencePM = DeviceProxy("pm/fluencectrl/1")

    pumpHor = fluencePM.pumpHor
    pumpVer = fluencePM.pumpVer
    refl = fluencePM.refl
    repRate = fluencePM.repRate

    self.output(
        "Fluence Settings: pumpHor = %.2f um | pumpVer = %.2f um |"
        "refl = %.2f %% | repRate = %.2f Hz",
        pumpHor,
        pumpVer,
        refl,
        repRate,
    )

    fluence = self.getPseudoMotor("fluence")
    [minFluence, maxFluence] = fluence.getPositionObj().getLimits()

    self.output(
        "Fluence Limits  : min = %.3f mJ/cm^2 | max = %.3f mJ/cm^2",
        minFluence,
        maxFluence,
    )


@imacro(
    [
        ["P0", Type.Float, Optional, "P0"],
        ["Pm", Type.Float, Optional, "Pm"],
        ["offset", Type.Float, Optional, "offset"],
        ["period", Type.Float, Optional, "period"],
    ]
)
def powerconf(self, P0, Pm, offset, period):
    """This sets the parameters of the power pseudo motor"""
    power = DeviceProxy("pm/powerctrl/1")

    if P0 is None:
        label, unit = "P0", "W"
        P0 = self.input(
            "Set the minimum power:",
            data_type=Type.Float,
            title="Minimum Power",
            key=label,
            unit=unit,
            default_value=power.P0,
            minimum=0.0,
            maximum=100000,
        )

    if Pm is None:
        label, unit = "Pm", "W"
        Pm = self.input(
            "Set the maximum power:",
            data_type=Type.Float,
            title="Maximum Power",
            key=label,
            unit=unit,
            default_value=power.Pm,
            minimum=0.0,
            maximum=100000,
        )

    if offset is None:
        label, unit = "offset", "deg"
        offset = self.input(
            "Set the radial offset:",
            data_type=Type.Float,
            title="Radial Offset",
            key=label,
            unit=unit,
            default_value=power.offset,
            minimum=-45,
            maximum=45,
        )

    if period is None:
        label, unit = "period", ""
        period = self.input(
            "Set the radial period:",
            data_type=Type.Float,
            title="Radial Period",
            key=label,
            unit=unit,
            default_value=power.period,
            minimum=0,
            maximum=2,
        )

    self.info("Update parameters of pseudo motor power")
    power.offset = offset
    power.period = period
    power.P0 = P0
    power.Pm = Pm

    self.execMacro("set_lim", "power", P0, (Pm + P0))
    self.execMacro("powerrep")


@macro()
def powerrep(self):
    # return all powerconf values
    power = DeviceProxy("pm/powerctrl/1")
    self.output(
        "Power Settings  : P0 = %.4f W | Pm = %.4f W |"
        "offset = %.2f deg | period = %.2f",
        power.P0,
        power.Pm,
        power.offset,
        power.period,
    )


