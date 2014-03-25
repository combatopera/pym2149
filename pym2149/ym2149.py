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

from reg import Reg, DerivedReg
from osc import ToneOsc, NoiseOsc, EnvOsc, TimerSynth
from dac import Level, Dac
from mix import BinMix
from nod import Container

stclock = 2000000
defaultscale = 8

class Registers:

  channels = 3

  def __init__(self):
    # Like the real thing we have 16 registers, this impl ignores the last 2:
    self.R = tuple(Reg(0) for i in xrange(16))
    # Clamping is authentic in all 3 cases, see qtonpzer, qnoispec, qenvpzer respectively.
    # TP, NP, EP are suitable for plugging into the formulas in the datasheet:
    TP = lambda f, r: max(1, ((r & 0x0f) << 8) | (f & 0xff))
    NP = lambda p: max(1, p & 0x1f)
    EP = lambda f, r: max(1, ((r & 0xff) << 8) | (f & 0xff))
    self.toneperiods = tuple(DerivedReg(TP, self.R[c * 2], self.R[c * 2 + 1]) for c in xrange(self.channels))
    self.noiseperiod = DerivedReg(NP, self.R[0x6])
    def flagxform(b):
      mask = 0x01 << b
      return lambda x: not (x & mask)
    self.toneflags = tuple(DerivedReg(flagxform(c), self.R[0x7]) for c in xrange(self.channels))
    self.noiseflags = tuple(DerivedReg(flagxform(self.channels + c), self.R[0x7]) for c in xrange(self.channels))
    self.fixedlevels = tuple(DerivedReg(lambda x: x & 0x0f, self.R[0x8 + c]) for c in xrange(self.channels))
    self.levelmodes = tuple(DerivedReg(lambda x: bool(x & 0x10), self.R[0x8 + c]) for c in xrange(self.channels))
    self.envperiod = DerivedReg(EP, self.R[0xB], self.R[0xC])
    self.envshape = DerivedReg(lambda x: x & 0x0f, self.R[0xD])
    self.tsfreqs = tuple(Reg(0) for _ in xrange(self.channels))
    self.tsflags = tuple(Reg(0) for _ in xrange(self.channels))

class YM2149(Registers, Container):

  def __init__(self, ampshare = None, scale = defaultscale, pause = False):
    Registers.__init__(self)
    # Chip-wide signals:
    noise = NoiseOsc(scale, self.noiseperiod)
    env = EnvOsc(scale, self.envperiod, self.envshape)
    # Digital channels from binary to level in [0, 31]:
    tones = [ToneOsc(scale, self.toneperiods[c]) for c in xrange(self.channels)]
    self.maskables = tones + [noise, env] # Maskable by mixer and level mode.
    binchans = [BinMix(tones[c], noise, self.toneflags[c], self.noiseflags[c]) for c in xrange(self.channels)]
    timersynths = [TimerSynth(self, self.tsfreqs[c]) for c in xrange(self.channels)]
    levels = [Level(self.levelmodes[c], self.fixedlevels[c], env, binchans[c], timersynths[c], self.tsflags[c]) for c in xrange(self.channels)]
    if ampshare is None:
      ampshare = self.channels
    Container.__init__(self, [Dac(level, ampshare) for level in levels])
    self.pause = pause

  def callimpl(self):
    result = Container.callimpl(self)
    if not self.pause:
      # Pass the block to any nodes that were masked:
      for maskable in self.maskables:
        maskable(self.block, True) # The masked flag tells the node we don't care about output.
    return result
