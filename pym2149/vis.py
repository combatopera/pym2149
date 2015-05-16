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

from pitch import Period, Freq
from di import types
from iface import Chip, Config
import sys

class Roll:

  shapes = ('\\_',) * 4 + ('/_',) * 4 + ('\\\\', '\\_', '\\/', u'\\\u203e', '//', u'/\u203e', '/\\', '/_')

  @types(Config, Chip)
  def __init__(self, config, chip):
    self.height = config.pianorollheight
    self.nomclock = config.nominalclock
    self.channels = config.chipchannels
    self.line = 0
    self.jump = "\x1b[%sA" % self.height
    self.format = ' | '.join(self.channels * ["%7s %1s %2s %1s %2s%1s%7s"])
    self.shapeversion = None
    self.chip = chip

  def update(self):
    if self.line == self.height:
      sys.stderr.write(self.jump)
      self.line = 0
    vals = []
    for c in xrange(self.channels):
      tone = self.chip.toneflags[c].value
      noise = self.chip.noiseflags[c].value
      env = self.chip.levelmodes[c].value
      level = self.chip.fixedlevels[c].value
      newshape = (self.shapeversion != self.chip.envshape.version)
      self.shapeversion = self.chip.envshape.version
      timereffect = self.chip.timers[c].effect.value is not None
      rhs = env or level
      if tone and rhs:
        vals.append(Period(self.chip.toneperiods[c].value).tonefreq(self.nomclock).pitch())
      else:
        vals.append('')
      if tone and noise and rhs:
        vals.append('&')
      else:
        vals.append('')
      if noise and rhs:
        vals.append(self.chip.noiseperiod.value)
      else:
        vals.append('')
      if (tone or noise) and rhs:
        vals.append('*')
      else:
        vals.append('')
      if timereffect and (env or level):
        if env:
          vals.append(self.shapes[self.chip.envshape.value])
        else:
          vals.append(level)
        vals.append('')
        vals.append(Freq(self.chip.timers[c].getfreq()).pitch())
      elif env:
        shape = self.chip.envshape.value
        vals.append(self.shapes[shape])
        vals.append(('', '~')[newshape])
        vals.append(Period(self.chip.envperiod.value).envfreq(self.nomclock, shape).pitch())
      elif level:
        vals.append(level)
        vals.append('')
        vals.append('')
      else:
        vals.append('')
        vals.append('')
        vals.append('')
    print >> sys.stderr, self.format % tuple(vals)
    self.line += 1
