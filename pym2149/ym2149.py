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

from .clock import ClockInfo
from .dac import Dac, Level
from .iface import AmpScale, Config
from .lfsr import Lfsr
from .mfp import mfpclock, MFPTimer
from .mix import BinMix
from .nod import Container
from .osc2 import EnvOsc, NoiseOsc, RToneOsc, Shape, ToneOsc
from .reg import Reg, VersionReg
from diapyr import types
import logging

log = logging.getLogger(__name__)
ym2149nzdegrees = 17, 14
# TP, NP and EP are suitable for plugging into the formulas in the datasheet:
TP = lambda f, r: ((r & 0x0f) << 8) | f
NP = lambda p: p & 0x1f
EP = lambda f, r: (r << 8) | f
getlevelmode = lambda l: bool(l & 0x10)

class MixerFlag:

    def __init__(self, bit):
        self.mask = 0x01 << bit

    def __call__(self, m):
        return not (m & self.mask)

class LogicalRegisters:

    @types(Config, ClockInfo)
    def __init__(self, config, clockinfo, minnoiseperiod = 1):
        channels = range(config.chipchannels)
        # TODO: Make effective tone period user-readable without exposing mintoneperiod.
        # Clamping 0 to 1 is authentic for all 3 kinds of period, see qtonpzer, qnoispec, qenvpzer respectively:
        self.toneperiods = [Reg(maxval = config.maxtoneperiod, minval = clockinfo.mintoneperiod) for _ in channels]
        self.noiseperiod = Reg(maxval = config.maxnoiseperiod, minval = minnoiseperiod)
        self.toneflags = [Reg() for _ in channels]
        self.noiseflags = [Reg() for _ in channels]
        self.fixedlevels = [Reg(maxval = 0x0f, minval = 0) for _ in channels]
        self.levelmodes = [Reg() for _ in channels]
        self.envshape = VersionReg(maxval = 0x0f, minval = 0)
        self.envperiod = Reg(maxval = config.maxenvperiod, minval = 1)
        initialmixerflag = MixerFlag(0)(0) # Result is the same whatever the bit.
        for c in channels:
            self.toneperiods[c].value = TP(0, 0)
            self.toneflags[c].value = initialmixerflag
            self.noiseflags[c].value = initialmixerflag
            self.fixedlevels[c].value = 0
            self.levelmodes[c].value = getlevelmode(0)
        self.noiseperiod.value = 0
        self.envperiod.value = EP(0, 0)
        self.envshape.value = 0
        self.timers = tuple(MFPTimer() for _ in channels)

    def flagsoff(self, chan):
        self.levelmodes[chan].value = 0 # Effectively the envelope flag.
        self.toneflags[chan].value = False
        self.noiseflags[chan].value = False
        self.timers[chan].effect.value = None

class PhysicalRegisters:

    supportedchannels = 3
    timers = property(lambda self: self.logical.timers)
    levelbase = 0x8

    @types(Config, LogicalRegisters)
    def __init__(self, config, logical):
        # XXX: Add reverse wiring?
        # Like the real thing we have 16 registers, this impl ignores the last 2:
        self.R = tuple(Reg() for _ in range(16)) # Assume all incoming values are in [0, 255].
        # We only have registers for the authentic number of channels:
        for c in range(min(self.supportedchannels, config.chipchannels)):
            logical.toneperiods[c].link(TP, self.R[c * 2], self.R[c * 2 + 1])
            logical.toneflags[c].link(MixerFlag(c), self.R[0x7])
            logical.noiseflags[c].link(MixerFlag(self.supportedchannels + c), self.R[0x7])
            logical.fixedlevels[c].link(lambda l: l & 0x0f, self.R[self.levelbase + c])
            logical.levelmodes[c].link(getlevelmode, self.R[self.levelbase + c])
        logical.noiseperiod.link(NP, self.R[0x6])
        logical.envperiod.link(EP, self.R[0xB], self.R[0xC])
        logical.envshape.link(lambda s: s & 0x0f, self.R[0xD])
        for r in self.R:
            r.value = 0
        self.logical = logical

class YM2149(Container):

    noiseshape = Shape(Lfsr(ym2149nzdegrees))

    @types(Config, ClockInfo, AmpScale, LogicalRegisters)
    def __init__(self, config, clockinfo, ampscale, logical):
        self.scale = clockinfo.scale
        channels = config.chipchannels
        self.oscpause = config.oscpause
        self.clock = clockinfo.implclock
        # Chip-wide signals:
        noise = NoiseOsc(self.scale, logical.noiseperiod, self.noiseshape)
        env = EnvOsc(self.scale, logical.envperiod, logical.envshape)
        # Digital channels from binary to level in [0, 31]:
        tones = [ToneOsc(self.scale, logical.toneperiods[c]) for c in range(channels)]
        rtones = [RToneOsc(mfpclock, self.clock, logical.timers[c]) for c in range(channels)]
        # XXX: Add rtones to maskables?
        self.maskables = tones + [noise, env] # Maskable by mixer and level mode.
        binchans = [BinMix(tones[c], noise, logical.toneflags[c], logical.noiseflags[c]) for c in range(channels)]
        levels = [Level(logical.levelmodes[c], logical.fixedlevels[c], env, binchans[c], rtones[c], logical.timers[c].effect) for c in range(channels)]
        super().__init__([Dac(level, ampscale.log2maxpeaktopeak, channels) for level in levels])

    def callimpl(self):
        result = super().callimpl()
        if not self.oscpause:
            # Pass the block to any nodes that were masked:
            for maskable in self.maskables:
                maskable(self.block, True) # The masked flag tells the node we don't care about output.
        return result
