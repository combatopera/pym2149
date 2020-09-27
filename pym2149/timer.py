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

from .iface import Timer
from .nod import Block
import logging

log = logging.getLogger(__name__)

class SimpleTimer(Timer):

    def __init__(self, clock):
        self.carryticks = 0
        self.clock = clock

    def blocksforperiod(self, refreshrate):
        available = self.carryticks + self.clock
        blockticks = int(round(available / refreshrate))
        self.carryticks = available - blockticks * refreshrate
        yield Block(blockticks)

    def __del__(self):
        if self.carryticks:
            log.warning("Non-zero carry on dispose: %s", self.carryticks)

class MinBlockRateTimer(SimpleTimer):

    def __init__(self, clock, minblockrate):
        # If division not exact, rate will slightly exceed given minimum:
        self.maxblocksize = int(clock // minblockrate)
        if not self.maxblocksize:
            raise Exception(clock, minblockrate)
        super().__init__(clock)

    def blocksforperiod(self, refreshrate):
        wholeperiodblock, = super().blocksforperiod(refreshrate)
        blockticks = wholeperiodblock.framecount
        while blockticks:
            size = min(blockticks, self.maxblocksize)
            b = Block(size)
            blockticks -= size
            yield b
