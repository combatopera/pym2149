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
import sys, logging, numpy as np, defaultconf
from pym2149.ym2149 import YM2149, defaultscale, stclock
from pym2149.out import WavWriter, WavBuf
from pym2149.mix import IdealMixer

log = logging.getLogger(__name__)

def getprocessconfig():
  return Config(sys.argv[1:])

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

  def __init__(self, args):
    # FIXME: Update the wiki.
    self.positional = args
    g = defaultconf.__dict__.copy()
    execfile('chipconf.py', g)
    statestride = g['statestride']
    self.scale = defaultscale // statestride
    if self.scale < 0 or defaultscale != self.scale * statestride:
        raise Exception("statestride must be a power of 2 and at most %s." % defaultscale)
    self.height = g['pianorollheightornone']
    self.panlaw = g['panlaw']
    self.outrate = g['outputrate']
    self.nominalclockornone = g['nominalclockornone']
    self.pause = g['oscpause']
    self.once = g['ignoreloop']
    self.stereo = g['stereo']
    self.clamp = g['freqclamp']

  def getnominalclock(self, altdefault = None):
    if self.nominalclockornone is not None:
      return self.nominalclockornone
    if altdefault is not None:
      return altdefault
    return stclock

  def createchip(self, nominalclock = None, log2maxpeaktopeak = 16):
    nominalclock = self.getnominalclock(nominalclock)
    clockdiv = 8 // self.scale
    if nominalclock % clockdiv:
      raise Exception("Clock %s not divisible by %s." % (nominalclock, clockdiv))
    clock = nominalclock // clockdiv
    clampoutrate = self.outrate if self.clamp else None
    chip = YM2149(clock, log2maxpeaktopeak, scale = self.scale, pause = self.pause, clampoutrate = clampoutrate)
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
    return [WavBuf(chip.clock, naive, self.outrate) for naive in naives]

  def createstream(self, chip, outpath):
    return WavWriter(WavBuf.multi(self.createfloatstream(chip)), outpath)

  def getheight(self, defaultheight):
    if self.height is not None:
      return self.height
    else:
      return defaultheight
