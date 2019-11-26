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

from .iface import Chip, Config, Tuning
from .lurlene import convenient
from .native.resid import NativeSID
from .reg import regproperty, Reg
from diapyr import types
from lurlene import topitch

PAL = 4.43361875e6 * 4 / 18
NTSC = 3.579545e6 * 4 / 14

class ChanProxy:

    degree = regproperty(lambda self: self.degreereg)
    control = regproperty(lambda self: self.controlreg)
    adsr = regproperty(lambda self: self.adsrreg)

    def __init__(self, nativeregs, chan, fclk, tuning):
        self.degreereg = Reg()
        self.pitchreg = Reg().link(topitch, self.degreereg)
        self.freqreg = Reg().link(tuning.freq, self.pitchreg)
        self.fnreg = Reg().link(lambda fout: max(0, min(0xffff, round(fout * (1 << 24) / fclk))), self.freqreg)
        Reg.link(nativeregs[chan * 7], lambda value: value & 0xff, self.fnreg)
        Reg.link(nativeregs[chan * 7 + 1], lambda value: value >> 8, self.fnreg)
        self.controlreg = Reg()
        Reg.link(nativeregs[chan * 7 + 4], lambda value: value & 0xff, self.controlreg)
        self.adsrreg = Reg()
        Reg.link(nativeregs[chan * 7 + 5], lambda value: (value >> 8) & 0xff, self.adsrreg)
        Reg.link(nativeregs[chan * 7 + 6], lambda value: value & 0xff, self.adsrreg)

@convenient(ChanProxy)
class ChipProxy:

    def __init__(self, chan, chanproxies):
        self._chanproxies = chanproxies[chan:] + chanproxies[:chan]

    def __getitem__(self, index):
        return self._chanproxies[index]

class SIDChip(Chip):

    class NativeReg:

        idle = True # No downstream links so always idle.

        def __init__(self, nativesid, index):
            self.nativesid = nativesid
            self.index = index

        def set(self, value):
            self.nativesid.write(self.index, value)

    param = 'sid'

    @types(Config, Tuning)
    def __init__(self, config, tuning):
        fclk = config.SID['clock']
        nativesid = NativeSID()
        nativeregs = [self.NativeReg(nativesid, index) for index in range(0x19)]
        chans = range(3)
        chanproxies = [ChanProxy(nativeregs, chan, fclk, tuning) for chan in chans]
        self.channels = [ChipProxy(chan, chanproxies) for chan in chans]

def configure(di):
    di.add(SIDChip)
