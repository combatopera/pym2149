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
from .clock import ClockInfo
from .iface import Chip, Config, Tuning, AmpScale
from .lurlene import convenient
from .minblep import MinBleps
from .native.resid import NativeSID
from .nod import Node
from .out import Translator, FloatStream
from .reg import regproperty, Reg
from .shapes import floatdtype
from diapyr import types
from lurlene import topitch
import numpy as np

PAL = 4.43361875e6 * 4 / 18
NTSC = 3.579545e6 * 4 / 14

class ChanProxy:

    degree = regproperty(lambda self: self.degreereg)
    pulsewidth = regproperty(lambda self: self.pulsewidthreg)
    control = regproperty(lambda self: self.controlreg)
    pulse = regproperty(lambda self: self.pulsereg)
    triangle = regproperty(lambda self: self.trianglereg)
    gate = regproperty(lambda self: self.gatereg)
    attack = regproperty(lambda self: self.attackreg)
    decay = regproperty(lambda self: self.decayreg)
    sustain = regproperty(lambda self: self.sustainreg)
    release = regproperty(lambda self: self.releasereg)

    def __init__(self, sidregs, chan, fclk, tuning):
        self.degreereg = Reg()
        self.pitchreg = Reg().link(topitch, self.degreereg)
        self.freqreg = Reg().link(tuning.freq, self.pitchreg)
        self.fnreg = Reg().link(lambda fout: max(0, min(0xffff, round(fout * (1 << 24) / fclk))), self.freqreg)
        sidregs[chan, 0].link(lambda fn: fn & 0xff, self.fnreg)
        sidregs[chan, 1].link(lambda fn: fn >> 8, self.fnreg)
        self.pulsewidthreg = Reg()
        self.pwnreg = Reg().link(lambda pwout: max(0, min(0xfff, round(pwout * 40.95))), self.pulsewidthreg)
        sidregs[chan, 2].link(lambda pwn: pwn & 0xff, self.pwnreg)
        sidregs[chan, 3].link(lambda pwn: pwn >> 8, self.pwnreg)
        self.controlreg = Reg(0)
        sidregs[chan, 4].link(lambda control: control & 0xff, self.controlreg)
        self.pulsereg = Reg()
        self.controlreg.mlink(0x40, lambda b: -b, self.pulsereg)
        self.trianglereg = Reg()
        self.controlreg.mlink(0x10, lambda b: -b, self.trianglereg)
        self.gatereg = Reg()
        self.controlreg.mlink(0x01, lambda gate: gate, self.gatereg)
        adreg = Reg(0)
        srreg = Reg(0)
        sidregs[chan, 5].link(lambda ad: ad, adreg)
        sidregs[chan, 6].link(lambda sr: sr, srreg)
        self.attackreg = Reg()
        self.decayreg = Reg()
        self.sustainreg = Reg()
        self.releasereg = Reg()
        adreg.mlink(0xf0, lambda attack: attack << 4, self.attackreg)
        adreg.mlink(0x0f, lambda decay: decay, self.decayreg)
        srreg.mlink(0xf0, lambda sustain: max(0, min(0xf, round(10 ** (sustain / 20) * 0xf))) << 4, self.sustainreg)
        srreg.mlink(0x0f, lambda release: release, self.releasereg)

@convenient(ChanProxy)
class ChipProxy:

    volume = regproperty(lambda self: self._sidregs.volumereg)

    def __init__(self, chan, chanproxies, sidregs):
        self._chanproxies = chanproxies[chan:] + chanproxies[:chan]
        self._sidregs = sidregs

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

class SIDStream(FloatStream):

    streamname = 'sid'

    @types(ClockInfo, AmpScale, SID, MinBleps)
    def __init__(self, clockinfo, ampscale, sid, minbleps):
        self.append(SIDBuf(clockinfo, ampscale, sid, minbleps))

class SIDRegs:

    class SIDReg:

        idle = True # No downstream links so always idle.

        def __init__(self, sid, index):
            self.sid = sid
            self.index = index

        def set(self, value):
            self.sid.write(self.index, value)

        def link(self, *args):
            Reg.link(self, *args)

    def __init__(self, sid):
        self.regs = [self.SIDReg(sid, index) for index in range(sid.regcount)]
        modevolreg = Reg(0)
        self.regs[0x18].link(lambda x: x, modevolreg)
        self.volumereg = Reg()
        modevolreg.mlink(0x0f, lambda volume: max(0, min(0xf, round(volume))), self.volumereg)

    def __getitem__(self, key):
        chan, offset = key
        return self.regs[chan * 7 + offset]

class SIDChip(Chip):

    param = 'sid'

    @types(Config, Tuning, SID)
    def __init__(self, config, tuning, sid):
        fclk = config.SID['clock']
        sidregs = SIDRegs(sid)
        chanproxies = [ChanProxy(sidregs, chan, fclk, tuning) for chan in range(sid.chancount)]
        self.channels = [ChipProxy(chan, chanproxies, sidregs) for chan in range(sid.chancount)]

def configure(di):
    di.add(SID)
    di.add(SIDStream)
    di.add(SIDChip)
