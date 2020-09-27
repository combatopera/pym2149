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

from .iface import Chip, Config, Prerecorded, Roll, Stream, Timer
from .ym2149 import PhysicalRegisters
from diapyr import types
from splut.bg import MainBackground

class Bundle:

    def __init__(self, prerecorded, registers):
        self.prerecorded = prerecorded
        self.registers = registers

    def __iter__(self):
        yield from self.prerecorded.frames(self.registers)

class LogicalBundle(Bundle):

    @types(Prerecorded, [Chip])
    def __init__(self, prerecorded, chips):
        super().__init__(prerecorded, {chip.param: chip.channels for chip in chips})

class PhysicalBundle(Bundle):

    @types(Prerecorded, PhysicalRegisters)
    def __init__(self, prerecorded, registers):
        super().__init__(prerecorded, registers)

class Player(MainBackground):

    @types(Config, Bundle, Roll, Timer, Stream)
    def __init__(self, config, bundle, roll, timer, stream):
        super().__init__(config)
        self.updaterate = config.updaterate
        self.bundle = bundle
        self.roll = roll
        self.timer = timer
        self.stream = stream

    def __call__(self):
        for _ in self.bundle:
            if self.quit:
                break
            self.roll.update()
            for b in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(b)
        self.stream.flush()
