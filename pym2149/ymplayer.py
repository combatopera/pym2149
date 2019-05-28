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

from .timer import Timer, SimpleTimer
from .vis import Roll
from .iface import Chip, Stream, Prerecorded, Config
from .ym2149 import ClockInfo
from bg import MainBackground
from diapyr import types

class SimpleChipTimer(SimpleTimer):

    @types(ClockInfo)
    def __init__(self, clockinfo):
        super().__init__(clockinfo.implclock)

class Player(MainBackground):

    @types(Config, Prerecorded, Chip, Roll, Timer, Stream)
    def __init__(self, config, prerecorded, chip, roll, timer, stream):
        super().__init__(config)
        self.updaterate = config.updaterate
        self.ym = prerecorded.ym
        self.chip = chip
        self.roll = roll
        self.timer = timer
        self.stream = stream

    def __call__(self):
        for frame in self.ym:
            if self.quit:
                break
            frame(self.chip)
            self.roll.update()
            for b in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(b)
        self.stream.flush()
