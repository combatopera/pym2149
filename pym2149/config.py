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
import sys, logging, numpy as np, os, anchor
from out import WavBuf
from mix import IdealMixer
from minblep import MinBleps
from lazyconf import Loader, View
from const import appconfigdir

log = logging.getLogger(__name__)

def getprocessconfig():
  return Config(sys.argv[1:])

class Config(View):

  def __init__(self, args):
    loader = Loader()
    View.__init__(self, loader)
    self.positional = args
    loader.load(os.path.join(os.path.dirname(anchor.__file__), 'defaultconf.py'))
    configspath = os.path.join(appconfigdir, 'configs')
    if os.path.exists(configspath):
      configs = ['defaults'] + sorted(os.listdir(configspath))
      for i, config in enumerate(configs):
        print >> sys.stderr, "%s) %s" % (i, config)
      sys.stderr.write('#? ')
      i = int(raw_input())
      if i:
        loader.load(os.path.join(configspath, configs[i]))

  def getamppair(self, loc):
    l = ((1 - loc) / 2) ** (self.panlaw / 6)
    r = ((1 + loc) / 2) ** (self.panlaw / 6)
    return l, r

  def createfloatstream(self, clockinfo, chip, log2maxpeaktopeak):
    if self.stereo:
      n = self.chipchannels
      locs = (np.arange(n) * 2 - (n - 1)) / (n - 1) * self.maxpan
      amppairs = [self.getamppair(loc) for loc in locs]
      chantoamps = zip(*amppairs)
      naives = [IdealMixer(chip, log2maxpeaktopeak, amps) for amps in chantoamps]
    else:
      naives = [IdealMixer(chip, log2maxpeaktopeak)]
    if self.outputrate != self.__getattr__('outputrate'):
      log.warn("Configured outputrate %s overriden to %s: %s", self.__getattr__('outputrate'), self.outputrateoverridelabel, self.outputrate)
    minbleps = MinBleps.loadorcreate(clockinfo.implclock, self.outputrate, None)
    return [WavBuf(naive, minbleps) for naive in naives]
