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
from .dac import NullEffect, PWMEffect, SinusEffect
from .iface import Config, Roll, Tuning
from .ym2149 import LogicalRegisters
from diapyr import types
from diapyr.util import singleton

@singleton
class NullRoll(Roll):

    def update(self):
        pass

class RollImpl(Roll):

    line = 0
    shapes = ('\\_',) * 4 + ('/_',) * 4 + ('\\\\', '\\_', '\\/', '\\\u203e', '//', '/\u203e', '/\\', '/_')
    shapeversion = None

    @types(Config, ClockInfo, LogicalRegisters, Tuning)
    def __init__(self, config, clock, chip, tuning):
        self.height = config.pianorollheight
        self.channels = config.chipchannels
        self.periods = config.showperiods # TODO LATER: Command line arg isn't converted to boolean.
        self.stream = config.rollstream
        self.mincents = config.rollmincents
        self.jump = f"\x1b[{self.height}A"
        self.format = ' | '.join(self.channels * ["%7s %1s %2s %1s %2s%1s%7s"])
        self.clock = clock
        self.chip = chip
        self.tuning = tuning

    def _pitchstr(self, freq):
        return self.tuning.pitch(freq).str(self.mincents)

    def _getvals(self, c):
        if self.chip.levelmodes[c].value or self.chip.fixedlevels[c].value:
            tone = self.chip.toneflags[c].value
            noise = self.chip.noiseflags[c].value
            if tone:
                toneperiod = self.chip.toneperiods[c].value
                yield toneperiod if self.periods else self._pitchstr(self.clock.tonefreq(toneperiod))
            else:
                yield ''
            yield '&' if tone and noise else ''
            yield self.chip.noiseperiod.value if noise else ''
            yield '*' if tone or noise else ''
        else:
            yield ''
            yield ''
            yield ''
            yield ''
        yield from self.effecttovals[self.chip.timers[c].effect.value](self, c)

    def _dacvals(self, c):
        if self.chip.levelmodes[c].value:
            shape = self.chip.envshape.value
            yield self.shapes[shape]
            yield '~' if self.shapeversion != self.chip.envshape.version else ''
            if self.periods:
                yield self.chip.envperiod.value
            else:
                yield self._pitchstr(self.clock.envfreq(self.chip.envperiod.value, shape))
        else:
            level = self.chip.fixedlevels[c].value
            yield level if level else ''
            yield ''
            yield ''

    def _synthvals(self, c):
        level = self.chip.fixedlevels[c].value
        if level:
            yield level
            yield ''
            yield self._pitchstr(self.chip.timers[c].getfreq())
        else:
            yield ''
            yield ''
            yield ''

    effecttovals = {
        NullEffect: _dacvals,
        PWMEffect: _synthvals,
        SinusEffect: _synthvals,
    }

    def update(self):
        if self.line == self.height:
            self.stream.write(self.jump)
            self.line = 0
        print(self.format % tuple(v for c in range(self.channels) for v in self._getvals(c)), file = self.stream)
        self.shapeversion = self.chip.envshape.version
        self.line += 1
