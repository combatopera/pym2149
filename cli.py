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
import sys, logging, getopt, numpy as np
from pym2149.ym2149 import YM2149, defaultscale, stclock
from pym2149.out import WavWriter, WavBuf
from pym2149.mix import IdealMixer

log = logging.getLogger(__name__)

class Config:

  @staticmethod
  def uniqueoption(options, keys, defaultval, xform):
    vals = [v for k, v in options if k in keys]
    if not vals:
      return defaultval
    v, = vals
    return xform(v)

  @staticmethod
  def booleanoption(options, keys):
    for k, _ in options:
      if k in keys:
        return True
    return False

  def __init__(self, args = sys.argv[1:]):
    options, self.args = getopt.getopt(args, 'q:H:l:r:k:p1sc', ['quant=', 'height=', 'law=', 'rate=', 'clock=', 'pause', 'once', 'stereo', 'clamp'])
    self.scale = defaultscale // (2 ** self.uniqueoption(options, ('-q', '--quant'), 0, int))
    self.height = self.uniqueoption(options, ('-H', '--height'), None, int)
    self.panlaw = self.uniqueoption(options, ('-l', '--law'), 3, float)
    self.outrate = self.uniqueoption(options, ('-r', '--rate'), 44100, int)
    self.nominalclockornone = self.uniqueoption(options, ('-k', '--clock'), None, int)
    self.pause = self.booleanoption(options, ('-p', '--pause'))
    self.once = self.booleanoption(options, ('-1', '--once'))
    self.stereo = self.booleanoption(options, ('-s', '--stereo'))
    self.clamp = self.booleanoption(options, ('-c', '--clamp'))

  def nominalclock(self, altdefault = None):
    if self.nominalclockornone is not None:
      return self.nominalclockornone
    if altdefault is not None:
      return stclock
    return stclock

  def createchip(self, nominalclock = None):
    nominalclock = self.nominalclock(nominalclock)
    clockdiv = 8 // self.scale
    if nominalclock % clockdiv:
      raise Exception("Clock %s not divisible by %s." % (nominalclock, clockdiv))
    clock = nominalclock // clockdiv
    clampoutrate = self.outrate if self.clamp else None
    chip = YM2149(clock, scale = self.scale, pause = self.pause, clampoutrate = clampoutrate)
    if self.scale != defaultscale:
      log.debug("Clock adjusted to %s to take advantage of non-zero control quant level.", chip.clock)
    return chip

  def amppair(self, loc):
    l = ((1 - loc) / 2) ** (self.panlaw / 6)
    r = ((1 + loc) / 2) ** (self.panlaw / 6)
    return l, r

  maxpan = .75

  def createfloatstream(self, chip):
    if self.stereo:
      n = chip.channels
      locs = (np.arange(n) * 2 - (n - 1)) / (n - 1) * self.maxpan
      amppairs = [self.amppair(loc) for loc in locs]
      chantoamps = zip(*amppairs)
      naives = [IdealMixer(chip, amps) for amps in chantoamps]
    else:
      naives = [IdealMixer(chip)]
    return WavBuf.multi(chip.clock, naives, self.outrate)

  def createstream(self, chip, outpath):
    return WavWriter(self.createfloatstream(chip), outpath)

  def getheight(self, defaultheight):
    if self.height is not None:
      return self.height
    else:
      return defaultheight
