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

from .clock import ClockInfo
from .dac import Level, Dac
from .iface import AmpScale, Config
from .lfsr import Lfsr
from .mfp import MFPTimer, mfpclock
from .mix import BinMix
from .nod import Container
from .osc2 import ToneOsc, NoiseOsc, Shape, EnvOsc, RToneOsc
from .reg import Reg, VersionReg
from diapyr import types
import logging

log = logging.getLogger(__name__)
ym2149nzdegrees = 17, 14

class LogicalRegisters:

    @types(Config, ClockInfo)
    def __init__(self, config, clockinfo):
        channels = range(config.chipchannels)
        self.toneperiods = [Reg(minval = clockinfo.mintoneperiod) for _ in channels]
        self.noiseperiod = Reg(minval = 1)
        self.toneflags = [Reg() for _ in channels]
        self.noiseflags = [Reg() for _ in channels]
        self.fixedlevels = [Reg() for _ in channels]
        self.levelmodes = [Reg() for _ in channels]
        self.envshape = VersionReg()
        self.envperiod = Reg(minval = 1)
        for c in channels:
            self.toneperiods[c].value = PhysicalRegisters.TP(0, 0)
            self.toneflags[c].value = PhysicalRegisters.MixerFlag(0)(0)
            self.noiseflags[c].value = PhysicalRegisters.MixerFlag(0)(0)
            self.fixedlevels[c].value = 0
            self.levelmodes[c].value = False
        self.noiseperiod.value = 0
        self.envperiod.value = 0
        self.envshape.value = 0
        self.timers = tuple(MFPTimer() for _ in channels)

    def flagsoff(self, chan):
        self.levelmodes[chan].value = 0 # Effectively the envelope flag.
        self.toneflags[chan].value = False
        self.noiseflags[chan].value = False
        self.timers[chan].effect.value = None

class PhysicalRegisters:

    class MixerFlag:

        def __init__(self, bit):
            self.mask = 0x01 << bit

        def __call__(self, m):
            return not (m & self.mask)

    supportedchannels = 3
    # Clamping 0 to 1 is authentic in all 3 cases, see qtonpzer, qnoispec, qenvpzer respectively.
    # TP, NP, EP are suitable for plugging into the formulas in the datasheet:
    TP = staticmethod(lambda f, r: (f & 0xff) | ((r & 0x0f) << 8))
    NP = staticmethod(lambda p: p & 0x1f)
    EP = staticmethod(lambda f, r: (f & 0xff) | ((r & 0xff) << 8))
    timers = property(lambda self: self.logical.timers)
    levelbase = 0x8

    @types(Config, LogicalRegisters)
    def __init__(self, config, logical):
        # TODO: Add reverse wiring.
        # Like the real thing we have 16 registers, this impl ignores the last 2:
        self.R = tuple(Reg() for _ in range(16))
        # We only have registers for the authentic number of channels:
        for c in range(min(self.supportedchannels, config.chipchannels)):
            logical.toneperiods[c].link(self.TP, self.R[c * 2], self.R[c * 2 + 1])
            logical.toneflags[c].link(self.MixerFlag(c), self.R[0x7])
            logical.noiseflags[c].link(self.MixerFlag(self.supportedchannels + c), self.R[0x7])
            logical.fixedlevels[c].link(lambda l: l & 0x0f, self.R[self.levelbase + c])
            logical.levelmodes[c].link(lambda l: bool(l & 0x10), self.R[self.levelbase + c])
        logical.noiseperiod.link(self.NP, self.R[0x6])
        logical.envperiod.link(self.EP, self.R[0xB], self.R[0xC])
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
