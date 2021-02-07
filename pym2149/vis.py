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
from .dac import DigiDrumEffect, NullEffect, PWMEffect, SinusEffect
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
    wavestartstr = '~'

    @types(Config, ClockInfo, LogicalRegisters, Tuning)
    def __init__(self, config, clock, chip, tuning):
        self.height = config.pianorollheight
        self.channels = config.chipchannels
        self.periods = config.showperiods # TODO LATER: Command line arg isn't converted to boolean.
        self.stream = config.rollstream
        self.mincents = config.rollmincents
        self.jump = f"\x1b[{self.height}A"
        self.format = ' | '.join(self.channels * ["%7s %1s %2s %1s %2s%1s%7s"])
        self.effects = [None] * self.channels
        self.clock = clock
        self.chip = chip
        self.tuning = tuning

    def _pitchstr(self, freq):
        return self.tuning.pitch(freq).str(self.mincents)

    def _effectstartstr(self, c):
        return self.wavestartstr if self.effects[c] is not self.chip.timers[c].effect.value else ''

    def _lhsvals(self, c):
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

    def _regularvals(self, c):
        yield from self._lhsvals(c)
        if self.chip.levelmodes[c].value:
            shape = self.chip.envshape.value
            envperiod = self.chip.envperiod.value
            yield self.shapes[shape]
            yield self.wavestartstr if self.shapeversion != self.chip.envshape.version else ''
            yield envperiod if self.periods else self._pitchstr(self.clock.envfreq(envperiod, shape))
        else:
            yield self.chip.fixedlevels[c].value or ''
            yield ''
            yield ''

    def _synthvals(self, c):
        yield from self._lhsvals(c)
        level = self.chip.fixedlevels[c].value
        if level:
            yield level
            yield self._effectstartstr(c)
            yield self._pitchstr(self.chip.timers[c].getfreq())
        else:
            yield ''
            yield '' # XXX: Indicate new effect even if we can't hear it?
            yield ''

    def _ddvals(self, c):
        yield ''
        yield ''
        yield ''
        yield ''
        yield '%%'
        yield self._effectstartstr(c)
        yield ''

    effecttypetovals = {
        DigiDrumEffect: _ddvals,
        type(NullEffect): _regularvals,
        type(PWMEffect): _synthvals,
        type(SinusEffect): _synthvals,
    }

    def _getvals(self, c):
        return self.effecttypetovals[type(self.chip.timers[c].effect.value)](self, c)

    def update(self):
        if self.line == self.height:
            self.stream.write(self.jump)
            self.line = 0
        print(self.format % tuple(v for c in range(self.channels) for v in self._getvals(c)), file = self.stream)
        self.shapeversion = self.chip.envshape.version
        for c in range(self.channels):
            self.effects[c] = self.chip.timers[c].effect.value
        self.line += 1
