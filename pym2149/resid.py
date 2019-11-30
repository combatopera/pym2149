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

from .buf import MasterBuf
from .iface import Chip, Config, Tuning
from .lurlene import convenient
from .native.resid import NativeSID
from .nod import BufNode
from .out import Translator
from .reg import regproperty, Reg
from .shapes import floatdtype
from diapyr import types
from lurlene import topitch
import numpy as np

PAL = 4.43361875e6 * 4 / 18
NTSC = 3.579545e6 * 4 / 14

class ChanProxy:

    degree = regproperty(lambda self: self.degreereg)
    control = regproperty(lambda self: self.controlreg)
    adsr = regproperty(lambda self: self.adsrreg)

    def __init__(self, sidregs, chan, fclk, tuning):
        self.degreereg = Reg()
        self.pitchreg = Reg().link(topitch, self.degreereg)
        self.freqreg = Reg().link(tuning.freq, self.pitchreg)
        self.fnreg = Reg().link(lambda fout: max(0, min(0xffff, round(fout * (1 << 24) / fclk))), self.freqreg)
        Reg.link(sidregs[chan * 7], lambda fn: fn & 0xff, self.fnreg)
        Reg.link(sidregs[chan * 7 + 1], lambda fn: fn >> 8, self.fnreg)
        self.controlreg = Reg()
        Reg.link(sidregs[chan * 7 + 4], lambda control: control & 0xff, self.controlreg)
        self.adsrreg = Reg()
        Reg.link(sidregs[chan * 7 + 5], lambda adsr: (adsr >> 8) & 0xff, self.adsrreg)
        Reg.link(sidregs[chan * 7 + 6], lambda adsr: adsr & 0xff, self.adsrreg)

@convenient(ChanProxy)
class ChipProxy:

    def __init__(self, chan, chanproxies):
        self._chanproxies = chanproxies[chan:] + chanproxies[:chan]

    def __getitem__(self, index):
        return self._chanproxies[index]

class SID(NativeSID):

    chancount = 3
    regcount = chancount * 7 + 4
    log2maxpeaktopeak = 16

    @types()
    def __init__(self):
        super().__init__()

class SIDBuf(Node):

    def __init__(self, clockinfo, ampscale, sid, minbleps):
        super().__init__()
        self.translator = Translator(clockinfo, minbleps)
        self.shortmaster = MasterBuf(np.short)
        self.outmaster = MasterBuf(floatdtype)
        self.ampscale = 2 ** (ampscale.log2maxpeaktopeak - sid.log2maxpeaktopeak)
        self.sid = sid

    def callimpl(self):
        _, outcount = self.translator.step(self.block.framecount)
        shortbuf = self.shortmaster.ensureandcrop(outcount)
        self.sid.clock(shortbuf.buf)
        outbuf = self.outmaster.ensureandcrop(outcount)
        outbuf.copybuf(shortbuf)
        outbuf.mul(self.ampscale)
        return outbuf

class SIDChip(Chip):

    class SIDReg:

        idle = True # No downstream links so always idle.

        def __init__(self, sid, index):
            self.sid = sid
            self.index = index

        def set(self, value):
            self.sid.write(self.index, value)

    param = 'sid'

    @types(Config, Tuning, SID)
    def __init__(self, config, tuning, sid):
        fclk = config.SID['clock']
        sidregs = [self.SIDReg(sid, index) for index in range(sid.regcount)]
        chanproxies = [ChanProxy(sidregs, chan, fclk, tuning) for chan in range(sid.chancount)]
        self.channels = [ChipProxy(chan, chanproxies) for chan in range(sid.chancount)]

def configure(di):
    di.add(SID)
    di.add(SIDBuf)
    di.add(SIDChip)
