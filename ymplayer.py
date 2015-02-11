#!/usr/bin/env python

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

from pym2149.timer import Timer
from pym2149.vis import Roll
from pym2149.iface import Chip, Stream, YMFile
from pym2149.di import types
from pym2149.ym2149 import ClockInfo
import threading, logging

log = logging.getLogger(__name__)

class Background:

    def start(self):
        self.quit = False
        self.thread = threading.Thread(target = self)
        self.thread.start()

    def stop(self):
        self.quit = True
        self.thread.join()

class ChipTimer(Timer):

    @types(ClockInfo)
    def __init__(self, clockinfo):
        Timer.__init__(self, clockinfo.implclock)

class Player(Background):

    @types(YMFile, Chip, Roll, Timer, Stream)
    def __init__(self, ymfile, chip, roll, timer, stream):
        self.ym = ymfile.ym
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
            for b in self.timer.blocksforperiod(self.ym.framefreq):
                self.stream.call(b)
        self.stream.flush()
