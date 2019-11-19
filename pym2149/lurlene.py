# Copyright 2014, 2018, 2019 Andrzej Cichocki

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

from .iface import Prerecorded
from .reg import regproperty, Reg
from lurlene import topitch
from lurlene.bridge import LiveCodingBridge
import logging

log = logging.getLogger(__name__)

def _convenience(name):
    def fget(self):
        return getattr(self._chanproxies[0], name)
    def fset(self, value):
        setattr(self._chanproxies[0], name, value)
    return property(fget, fset)

class ChanProxy:

    tonefreq = regproperty(lambda self: self.tonefreqreg)
    level = regproperty(lambda self: self.levelreg)
    noiseflag = regproperty(lambda self: self._chip.noiseflags[self._chan])
    toneflag = regproperty(lambda self: self._chip.toneflags[self._chan])
    toneperiod = regproperty(lambda self: self.toneperiodreg)
    tonepitch = regproperty(lambda self: self.tonepitchreg)
    tonedegree = regproperty(lambda self: self.tonedegreereg)
    envflag = regproperty(lambda self: self._chip.levelmodes[self._chan])

    def __init__(self, chip, chan, clock, tuning):
        self.tonedegreereg = Reg()
        self.tonepitchreg = Reg().link(topitch, self.tonedegreereg)
        self.tonefreqreg = Reg().link(tuning.freq, self.tonepitchreg)
        self.toneperiodreg = Reg().link(clock.toneperiod, self.tonefreqreg)
        chip.toneperiods[chan].link(round, self.toneperiodreg)
        self.levelreg = Reg()
        chip.fixedlevels[chan].link(round, self.levelreg)
        self._chip = chip
        self._chan = chan

class ChipRegs:

    def __init__(self, chip, clock, tuning):
        self.noisefreqreg = Reg()
        self.noiseperiodreg = Reg().link(clock.noiseperiod, self.noisefreqreg)
        chip.noiseperiod.link(round, self.noiseperiodreg)
        self.envdegreereg = Reg()
        self.envpitchreg = Reg().link(topitch, self.envdegreereg)
        self.envfreqreg = Reg().link(tuning.freq, self.envpitchreg)
        self.envperiodreg = Reg().link(lambda f, s: clock.envperiod(f, s), self.envfreqreg, chip.envshape)
        chip.envperiod.link(round, self.envperiodreg)

class ChipProxy:

    noiseperiod = regproperty(lambda self: self._chipregs.noiseperiodreg)
    envshape = regproperty(lambda self: self._chip.envshape)
    envperiod = regproperty(lambda self: self._chipregs.envperiodreg)
    envpitch = regproperty(lambda self: self._chipregs.envpitchreg)
    envdegree = regproperty(lambda self: self._chipregs.envdegreereg)
    noisefreq = regproperty(lambda self: self._chipregs.noisefreqreg)
    envfreq = regproperty(lambda self: self._chipregs.envfreqreg)

    def __init__(self, chip, chan, chanproxies, chipregs):
        self._chanproxies = chanproxies[chan:] + chanproxies[:chan]
        self._chip = chip
        self._chipregs = chipregs

    def __getitem__(self, index):
        return self._chanproxies[index]

    def noisepriority(self):
        return not any(chan.noiseflag for chan in self._chanproxies[1:])

for name in dir(ChanProxy):
    if '_' != name[0]:
        setattr(ChipProxy, name, _convenience(name))
del name

class LurleneBridge(LiveCodingBridge, Prerecorded): pass
