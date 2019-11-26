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

from .iface import Chip
from .lurlene import convenient
from .native.resid import NativeSID
from .reg import regproperty, Reg
from diapyr import types

class ChanProxy:

    control = regproperty(lambda self: self.controlreg)

    def __init__(self, nativeregs, chan):
        self.controlreg = Reg()
        Reg.link(nativeregs[chan * 7 + 4], lambda value: max(0, min(0xff, round(value))), self.controlreg)

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

    @types()
    def __init__(self):
        nativesid = NativeSID()
        nativeregs = [self.NativeReg(nativesid, index) for index in range(0x19)]
        chans = range(3)
        chanproxies = [ChanProxy(nativeregs, chan) for chan in chans]
        self.channels = [ChipProxy(chan, chanproxies) for chan in chans]

def configure(di):
    di.add(SIDChip)
