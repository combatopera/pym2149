# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

from .reg import Reg, VersionReg

prescalers = {1 + i: v for i, v in enumerate([4, 10, 16, 50, 64, 100, 200])}
mfpclock = 2457600

class MFPTimer:

    def __init__(self):
        self.wavelength = Reg(2) # TODO LATER: Other shapes will have different numbers of steps.
        self.control = Reg()
        self.data = Reg()
        # TODO LATER: Verify that TDR 0 indeed behaves like 0x100.
        self.effectivedata = Reg().link(lambda tdr: tdr if tdr else 0x100, self.data)
        self.control.value = 0
        self.data.value = 0
        self.effect = VersionReg(None)
        self.control_data = Reg()
        self.control.link(lambda cd: cd[0], self.control_data)
        self.data.link(lambda cd: cd[1], self.control_data)
        self.freq = Reg()
        # XXX: Should change of wavelength trigger this link?
        self.control_data.link(self.findtcrtdr, self.freq)
        self.prescalerornone = Reg().link(lambda tcr: prescalers.get(tcr), self.control)

    def update(self, tcr, tdr, effect):
        self.control_data.value = tcr, tdr
        if type(effect) != type(self.effect.value):
            self.effect.value = effect

    def findtcrtdr(self, freq):
        diff = None
        for tcr, prescaler in prescalers.items(): # XXX: Do we care about non-determinism?
            prescaler *= self.wavelength.value # Avoid having to multiply twice.
            etdr = int(round(mfpclock / (freq * prescaler)))
            if 1 <= etdr and etdr <= 0x100:
                d = abs(mfpclock / (etdr * prescaler) - freq)
                if diff is None or d < diff:
                    tcrtdr = tcr, etdr & 0xff
                    diff = d
        return tcrtdr

    def getnormperiod(self):
        return prescalers[self.control.value] * self.effectivedata.value * self.wavelength.value

    def getfreq(self): # Currently only called when effect is not None.
        return mfpclock / self.getnormperiod()
