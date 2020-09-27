# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .clock import ClockInfo
from .iface import Config, Roll, Tuning
from .ym2149 import LogicalRegisters
from diapyr import types
from diapyr.util import singleton

@singleton
class NullRoll(Roll):

    def update(self):
        pass

class RollImpl(Roll):

    shapes = ('\\_',) * 4 + ('/_',) * 4 + ('\\\\', '\\_', '\\/', '\\\u203e', '//', '/\u203e', '/\\', '/_')

    @types(Config, ClockInfo, LogicalRegisters, Tuning)
    def __init__(self, config, clock, chip, tuning):
        self.height = config.pianorollheight
        self.channels = config.chipchannels
        self.periods = config.showperiods # TODO LATER: Command line arg isn't converted to boolean.
        self.stream = config.rollstream
        self.mincents = config.rollmincents
        self.line = 0
        self.jump = "\x1b[%sA" % self.height
        self.format = ' | '.join(self.channels * ["%7s %1s %2s %1s %2s%1s%7s"])
        self.shapeversion = None
        self.clock = clock
        self.chip = chip
        self.tuning = tuning

    def update(self):
        if self.line == self.height:
            self.stream.write(self.jump)
            self.line = 0
        vals = []
        def appendpitch(freq):
            vals.append(self.tuning.pitch(freq).str(self.mincents))
        for c in range(self.channels):
            tone = self.chip.toneflags[c].value
            noise = self.chip.noiseflags[c].value
            env = self.chip.levelmodes[c].value
            level = self.chip.fixedlevels[c].value
            newshape = (self.shapeversion != self.chip.envshape.version)
            self.shapeversion = self.chip.envshape.version
            timereffect = self.chip.timers[c].effect.value is not None
            rhs = env or level
            if tone and rhs:
                if self.periods:
                    vals.append(self.chip.toneperiods[c].value)
                else:
                    appendpitch(self.clock.tonefreq(self.chip.toneperiods[c].value))
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
                appendpitch(self.chip.timers[c].getfreq())
            elif env:
                shape = self.chip.envshape.value
                vals.append(self.shapes[shape])
                vals.append(('', '~')[newshape])
                if self.periods:
                    vals.append(self.chip.envperiod.value)
                else:
                    appendpitch(self.clock.envfreq(self.chip.envperiod.value, shape))
            elif level:
                vals.append(level)
                vals.append('')
                vals.append('')
            else:
                vals.append('')
                vals.append('')
                vals.append('')
        print(self.format % tuple(vals), file = self.stream)
        self.line += 1
