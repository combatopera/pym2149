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
import sys, logging, getopt
from pym2149.ym2149 import YM2149, defaultscale
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
    options, self.args = getopt.getopt(args, 'q:H:p1s', ['quant=', 'height=', 'pause', 'once', 'stereo'])
    self.scale = defaultscale // (2 ** self.uniqueoption(options, ('-q', '--quant'), 0, int))
    self.height = self.uniqueoption(options, ('-H', '--height'), None, int)
    self.pause = self.booleanoption(options, ('-p', '--pause'))
    self.once = self.booleanoption(options, ('-1', '--once'))
    self.stereo = self.booleanoption(options, ('-s', '--stereo'))

  def createchip(self, nominalclock, **kwargs):
    chip = YM2149(scale = self.scale, pause = self.pause, **kwargs)
    chip.clock = int(round(nominalclock * self.scale / 8))
    if self.scale != defaultscale:
      log.debug("Clock adjusted to %s to take advantage of non-zero control quant level.", chip.clock)
    return chip

  def createstream(self, chip, outpath):
    if self.stereo:
      midamp = .5 # TODO: Adjust.
      naives = [IdealMixer(chip, amps) for amps in ([1, midamp, 0], [0, midamp, 1])]
    else:
      naives = [IdealMixer(chip)]
    return WavWriter([WavBuf(chip.clock, naive) for naive in naives], outpath)

  def getheight(self, defaultheight):
    if self.height is not None:
      return self.height
    else:
      return defaultheight
