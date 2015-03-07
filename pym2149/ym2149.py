# Copyright 2014 Andrzej Cichocki

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

from __future__ import division
from reg import Reg, DerivedReg
from osc import ToneOsc, NoiseDiffs, NoiseOsc, EnvOsc, TimerSynth
from dac import Level, Dac
from mix import BinMix
from nod import Container
from fractions import Fraction
from iface import AmpScale, Chip, YMFile, Config
from di import types
import logging

log = logging.getLogger(__name__)

stclock = 2000000
defaultscale = 8
ym2149nzdegrees = 17, 14

class Registers:

  def __init__(self, clockinfo, channels):
    # Like the real thing we have 16 registers, this impl ignores the last 2:
    self.R = tuple(Reg(0) for i in xrange(16))
    # Clamping 0 to 1 is authentic in all 3 cases, see qtonpzer, qnoispec, qenvpzer respectively.
    # TP, NP, EP are suitable for plugging into the formulas in the datasheet:
    TP = lambda f, r: max(clockinfo.mintoneperiod, ((r & 0x0f) << 8) | (f & 0xff))
    NP = lambda p: max(1, p & 0x1f)
    EP = lambda f, r: max(1, ((r & 0xff) << 8) | (f & 0xff))
    self.toneperiods = tuple(DerivedReg(TP, self.R[c * 2], self.R[c * 2 + 1]) for c in xrange(channels))
    self.noiseperiod = DerivedReg(NP, self.R[0x6])
    def flagxform(b):
      mask = 0x01 << b
      return lambda x: not (x & mask)
    self.toneflags = tuple(DerivedReg(flagxform(c), self.R[0x7]) for c in xrange(channels))
    self.noiseflags = tuple(DerivedReg(flagxform(channels + c), self.R[0x7]) for c in xrange(channels))
    self.fixedlevels = tuple(DerivedReg(lambda x: x & 0x0f, self.R[0x8 + c]) for c in xrange(channels))
    self.levelmodes = tuple(DerivedReg(lambda x: bool(x & 0x10), self.R[0x8 + c]) for c in xrange(channels))
    self.envperiod = DerivedReg(EP, self.R[0xB], self.R[0xC])
    self.envshape = DerivedReg(lambda x: x & 0x0f, self.R[0xD])
    # TODO: Rename to rtone and make configurable.
    self.tsfreqs = tuple(Reg(Fraction(0)) for _ in xrange(channels))
    self.tsflags = tuple(Reg(0) for _ in xrange(channels))

class ClockInfo:

  @types(Config, YMFile)
  def __init__(self, config, ymfile = None):
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
    clampoutrate = config.outputrate if config.freqclamp else None
    self.mintoneperiod = max(self.toneperiodclampor0(clampoutrate), 1) if (clampoutrate is not None) else 1
    log.debug("Minimum tone period: %s", self.mintoneperiod)

  def toneperiodclampor0(self, outrate):
    # Largest period with frequency strictly greater than Nyquist, or 0 if there isn't one:
    return (self.implclock - 1) // (self.scale * outrate)

class YM2149(Registers, Container, Chip):

  @types(Config, ClockInfo, AmpScale)
  def __init__(self, config, clockinfo, ampscale):
    self.scale = clockinfo.scale
    channels = config.chipchannels
    self.oscpause = config.oscpause
    self.clock = clockinfo.implclock
    Registers.__init__(self, clockinfo, channels)
    # Chip-wide signals:
    noise = NoiseOsc(self.scale, self.noiseperiod, NoiseDiffs(ym2149nzdegrees))
    env = EnvOsc(self.scale, self.envperiod, self.envshape)
    # Digital channels from binary to level in [0, 31]:
    tones = [ToneOsc(self.scale, self.toneperiods[c]) for c in xrange(channels)]
    timersynths = [TimerSynth(self.clock, self.tsfreqs[c]) for c in xrange(channels)]
    # We don't add timersynths to maskables as it makes sense to pause them when not in use:
    self.maskables = tones + [noise, env] # Maskable by mixer and level mode.
    binchans = [BinMix(tones[c], noise, self.toneflags[c], self.noiseflags[c]) for c in xrange(channels)]
    levels = [Level(self.levelmodes[c], self.fixedlevels[c], env, binchans[c], timersynths[c], self.tsflags[c]) for c in xrange(channels)]
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
    self.tsflags[chan].value = False
