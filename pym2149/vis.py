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

from .pitch import Period, Freq
from diapyr import types
from .iface import Chip, Config, Tuning
from functools import partial
import sys

class Roll:

    shapes = ('\\_',) * 4 + ('/_',) * 4 + ('\\\\', '\\_', '\\/', '\\\u203e', '//', '/\u203e', '/\\', '/_')

    @types(Config, Chip, Tuning)
    def __init__(self, config, chip, tuning):
        self.height = config.pianorollheight
        self.nomclock = config.nominalclock
        self.channels = config.chipchannels
        self.line = 0
        self.jump = "\x1b[%sA" % self.height
        self.format = ' | '.join(self.channels * ["%7s %1s %2s %1s %2s%1s%7s"])
        self.shapeversion = None
        self.chip = chip
        self.tuning = tuning

    def update(self, print = partial(print, file = sys.stderr), mincents = 10):
        if self.line == self.height:
            sys.stderr.write(self.jump)
            self.line = 0
        vals = []
        def appendpitch(freq):
            vals.append(self.tuning.pitch(freq).str(mincents))
        for c in range(self.channels):
            tone = self.chip.toneflags[c].value
            noise = self.chip.noiseflags[c].value
            env = self.chip.levelmodes[c].value
            level = self.chip.fixedlevels[c].value
            newshape = (self.shapeversion != self.chip.envshapereg.version)
            self.shapeversion = self.chip.envshapereg.version
            timereffect = self.chip.timers[c].effect.value is not None
            rhs = env or level
            if tone and rhs:
                appendpitch(Period(self.chip.toneperiods[c].value).tonefreq(self.nomclock))
            else:
                vals.append('')
            if tone and noise and rhs:
                vals.append('&')
            else:
                vals.append('')
            if noise and rhs:
                vals.append(self.chip.noiseperiod)
            else:
                vals.append('')
            if (tone or noise) and rhs:
                vals.append('*')
            else:
                vals.append('')
            if timereffect and (env or level):
                if env:
                    vals.append(self.shapes[self.chip.envshape])
                else:
                    vals.append(level)
                vals.append('')
                appendpitch(Freq(self.chip.timers[c].getfreq()))
            elif env:
                shape = self.chip.envshape
                vals.append(self.shapes[shape])
                vals.append(('', '~')[newshape])
                appendpitch(Period(self.chip.envperiod).envfreq(self.nomclock, shape))
            elif level:
                vals.append(level)
                vals.append('')
                vals.append('')
            else:
                vals.append('')
                vals.append('')
                vals.append('')
        print(self.format % tuple(vals))
        self.line += 1
