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

from .dac import NullEffect
from .reg import Reg

prescalers = {1 + i: v for i, v in enumerate([4, 10, 16, 50, 64, 100, 200])}
mfpclock = 2457600

class MFPTimer:

    def __init__(self):
        self.control = Reg()
        self.data = Reg()
        # TODO LATER: Verify that TDR 0 indeed behaves like 0x100.
        self.effectivedata = Reg().link(lambda tdr: tdr if tdr else 0x100, self.data)
        self.control.value = 0
        self.data.value = 0
        self.effect = Reg(NullEffect)
        self.control_data = Reg()
        self.control.link(lambda cd: cd[0], self.control_data)
        self.data.link(lambda cd: cd[1], self.control_data)
        self.freq = Reg()
        # XXX: Should change of wavelength trigger this link?
        self.control_data.link(self._findtcrtdr, self.freq)
        self.prescalerornone = Reg().link(lambda tcr: prescalers.get(tcr), self.control)
        self.repeat = Reg().link(lambda _: None, self.effect)

    def update(self, tcr, tdr, effect):
        self.control_data.value = tcr, tdr
        self.effect.value = effect

    def _findtcrtdr(self, freq):
        if not freq:
            return 0, self.data.value # Stop timer.
        diff = float('inf')
        for tcr, prescaler in prescalers.items():
            prescaler *= self.effect.value.wavelength # Avoid having to multiply twice.
            etdr = int(round(mfpclock / (freq * prescaler)))
            if 1 <= etdr and etdr <= 0x100:
                d = abs(mfpclock / (etdr * prescaler) - freq)
                if d < diff:
                    tcrtdr = tcr, etdr & 0xff
                    diff = d
        return tcrtdr

    def _getnormperiod(self):
        return prescalers[self.control.value] * self.effectivedata.value * self.effect.value.wavelength

    def getfreq(self): # Currently only called when effect is not None.
        return mfpclock / self._getnormperiod()
