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
import sys, logging, numpy as np, defaultconf, os
from pym2149.ym2149 import YM2149, defaultscale
from pym2149.out import WavWriter, WavBuf
from pym2149.mix import IdealMixer
from pym2149.minblep import MinBleps

log = logging.getLogger(__name__)

def getprocessconfig():
  return Config(sys.argv[1:])

class Config:

  def __init__(self, args):
    self.positional = args
    g = defaultconf.__dict__.copy()
    if os.path.exists('chipconf.py'):
      execfile('chipconf.py', g)
    underclock = g['underclock']
    if underclock < 1 or defaultscale % underclock:
      raise Exception("underclock must be a factor of %s." % defaultscale)
    self.scale = defaultscale // underclock
    self.pianorollheightornone = g['pianorollheightornone']
    self.panlaw = g['panlaw']
    self.useroutputrate = g['outputrate']
    self.defaultclock = g['defaultclock']
    self.clockoverrideornone = g['clockoverrideornone']
    self.oscpause = g['oscpause']
    self.ignoreloop = g['ignoreloop']
    self.stereo = g['stereo']
    self.freqclamp = g['freqclamp']
    self.maxpan = g['maxpan']
    self.patches = g['patches']
    self.outputratewarningarmed = True
    self.outputrateoverride = None

  def getnominalclock(self, contextclockornone = None):
    if self.clockoverrideornone is not None:
      if contextclockornone is not None:
        log.info("Context clock %s overridden to: %s", contextclockornone, self.clockoverrideornone)
      return self.clockoverrideornone
    if contextclockornone is not None:
      return contextclockornone
    return self.defaultclock

  def getoutputrate(self):
    if self.outputrateoverride is not None:
      if self.outputratewarningarmed and self.useroutputrate != self.outputrateoverride:
        log.warn("Configured outputrate %s overriden to %s: %s", self.useroutputrate, self.outputrateoverridelabel, self.outputrateoverride)
        self.outputratewarningarmed = False
      return self.outputrateoverride
    return self.useroutputrate

  def createchip(self, contextclockornone = None, log2maxpeaktopeak = 16):
    nominalclock = self.getnominalclock(contextclockornone)
    underclock = defaultscale // self.scale
    if nominalclock % underclock:
      raise Exception("Clock %s not divisible by underclock %s." % (nominalclock, underclock))
    clock = nominalclock // underclock
    clampoutrate = self.getoutputrate() if self.freqclamp else None
    chip = YM2149(clock, log2maxpeaktopeak, scale = self.scale, oscpause = self.oscpause, clampoutrate = clampoutrate)
    if self.scale != defaultscale:
      log.debug("Clock adjusted to %s to take advantage of non-trivial underclock.", chip.clock)
    return chip

  def amppair(self, loc):
    l = ((1 - loc) / 2) ** (self.panlaw / 6)
    r = ((1 + loc) / 2) ** (self.panlaw / 6)
    return l, r

  def createfloatstream(self, chip):
    if self.stereo:
      n = chip.channels
      locs = (np.arange(n) * 2 - (n - 1)) / (n - 1) * self.maxpan
      amppairs = [self.amppair(loc) for loc in locs]
      chantoamps = zip(*amppairs)
      naives = [IdealMixer(chip, amps) for amps in chantoamps]
    else:
      naives = [IdealMixer(chip)]
    minbleps = MinBleps(chip.clock, self.getoutputrate(), None)
    return [WavBuf(naive, minbleps) for naive in naives]

  def createstream(self, chip, outpath):
    return WavWriter(WavBuf.multi(self.createfloatstream(chip)), outpath)

  def getheight(self, defaultheight):
    if self.pianorollheightornone is not None:
      return self.pianorollheightornone
    else:
      return defaultheight
