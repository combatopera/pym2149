# Copyright 2014, 2018 Andrzej Cichocki

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
from .osc2 import ToneOsc, NoiseOsc, Shape, EnvOsc, RToneOsc
from .dac import Level, Dac
from .mix import BinMix
from .nod import Container
from .iface import AmpScale, Chip, YMFile, Config, Platform
from diapyr import types
from .mfp import MFPTimer, mfpclock
from .lfsr import Lfsr
import logging

log = logging.getLogger(__name__)

stclock = 2000000
spectrum128crystal = 17734470 # Correct according to service manual.
spectrumclock = spectrum128crystal // 10
defaultscale = 8
ym2149nzdegrees = 17, 14

class MixerFlag:

  def __init__(self, bit):
    self.mask = 0x01 << bit

  def __call__(self, m):
    return not (m & self.mask)

class Registers:

  supportedchannels = 3

  def __init__(self, clockinfo, confchannels):
    # TODO: Add reverse wiring.
    # Like the real thing we have 16 registers, this impl ignores the last 2:
    self.R = tuple(Reg() for _ in range(16))
    # Clamping 0 to 1 is authentic in all 3 cases, see qtonpzer, qnoispec, qenvpzer respectively.
    # TP, NP, EP are suitable for plugging into the formulas in the datasheet:
    TP = lambda f, r: (f & 0xff) | ((r & 0x0f) << 8)
    NP = lambda p: p & 0x1f
    EP = lambda f, r: (f & 0xff) | ((r & 0xff) << 8)
    self.toneperiods = [Reg(minval = clockinfo.mintoneperiod) for _ in range(confchannels)]
    clampedchannels = min(self.supportedchannels, confchannels) # We only have registers for the authentic number of channels.
    for c in range(clampedchannels):
      self.toneperiods[c].link(TP, self.R[c * 2], self.R[c * 2 + 1])
    self.noiseperiod = Reg(minval = 1).link(NP, self.R[0x6])
    self.toneflags = [Reg() for _ in range(confchannels)]
    self.noiseflags = [Reg() for _ in range(confchannels)]
    self.fixedlevels = [Reg() for _ in range(confchannels)]
    self.levelmodes = [Reg() for _ in range(confchannels)]
    for c in range(clampedchannels):
      self.toneflags[c].link(MixerFlag(c), self.R[0x7])
      self.noiseflags[c].link(MixerFlag(self.supportedchannels + c), self.R[0x7])
      self.fixedlevels[c].link(lambda l: l & 0x0f, self.R[0x8 + c])
      self.levelmodes[c].link(lambda l: bool(l & 0x10), self.R[0x8 + c])
    self.envperiod = Reg(minval = 1).link(EP, self.R[0xB], self.R[0xC])
    self.envshape = VersionReg().link(lambda s: s & 0x0f, self.R[0xD])
    for r in self.R:
      r.value = 0
    for c in range(self.supportedchannels, confchannels):
      # These won't have been inited via the registers:
      self.toneperiods[c].value = TP(0, 0)
      self.toneflags[c].value = MixerFlag(0)(0)
      self.noiseflags[c].value = MixerFlag(0)(0)
      self.fixedlevels[c].value = 0
      self.levelmodes[c].value = False
    self.timers = tuple(MFPTimer() for _ in range(confchannels))

class ClockInfo:

  @types(Config, Platform, YMFile)
  def __init__(self, config, platform, ymfile = None):
    if config.nominalclock % config.underclock:
      raise Exception("Clock %s not divisible by underclock %s." % (config.nominalclock, config.underclock))
    self.implclock = config.nominalclock // config.underclock
    if ymfile is not None and config.nominalclock != ymfile.nominalclock:
      log.info("Context clock %s overridden to: %s", ymfile.nominalclock, config.nominalclock)
    if self.implclock != config.nominalclock:
      log.debug("Clock adjusted to %s to take advantage of non-trivial underclock.", self.implclock)
    if config.underclock < 1 or defaultscale % config.underclock:
      raise Exception("underclock must be a factor of %s." % defaultscale)
    self.scale = defaultscale // config.underclock
    if config.freqclamp:
      # The 0 case just means that 1 is audible:
      self.mintoneperiod = max(1, self.toneperiodclampor0(platform.outputrate))
      log.debug("Minimum tone period: %s", self.mintoneperiod)
    else:
      self.mintoneperiod = 1

  def toneperiodclampor0(self, outrate):
    # Largest period with frequency strictly greater than Nyquist, or 0 if there isn't one:
    return (self.implclock - 1) // (self.scale * outrate)

class YM2149(Registers, Container, Chip):

  noiseshape = Shape(Lfsr(ym2149nzdegrees))

  @types(Config, ClockInfo, AmpScale)
  def __init__(self, config, clockinfo, ampscale):
    self.scale = clockinfo.scale
    channels = config.chipchannels
    self.oscpause = config.oscpause
    self.clock = clockinfo.implclock
    Registers.__init__(self, clockinfo, channels)
    # Chip-wide signals:
    noise = NoiseOsc(self.scale, self.noiseperiod, self.noiseshape)
    env = EnvOsc(self.scale, self.envperiod, self.envshape)
    # Digital channels from binary to level in [0, 31]:
    tones = [ToneOsc(self.scale, self.toneperiods[c]) for c in range(channels)]
    rtones = [RToneOsc(mfpclock, self.clock, self.timers[c]) for c in range(channels)]
    # XXX: Add rtones to maskables?
    self.maskables = tones + [noise, env] # Maskable by mixer and level mode.
    binchans = [BinMix(tones[c], noise, self.toneflags[c], self.noiseflags[c]) for c in range(channels)]
    levels = [Level(self.levelmodes[c], self.fixedlevels[c], env, binchans[c], rtones[c], self.timers[c].effect) for c in range(channels)]
    Container.__init__(self, [Dac(level, ampscale.log2maxpeaktopeak, channels) for level in levels])

  def callimpl(self):
    result = Container.callimpl(self)
    if not self.oscpause:
      # Pass the block to any nodes that were masked:
      for maskable in self.maskables:
        maskable(self.block, True) # The masked flag tells the node we don't care about output.
    return result

  def flagsoff(self, chan):
    self.levelmodes[chan].value = 0 # Effectively the envelope flag.
    self.toneflags[chan].value = False
    self.noiseflags[chan].value = False
    self.timers[chan].effect.value = None
