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
from iface import Config
from di import types
from bg import SimpleBackground
import time

class PLL(SimpleBackground):

    @staticmethod
    def take(v):
        w = v[:]
        del v[:len(w)]
        return w

    @types(Config)
    def __init__(self, config):
        self.updateperiod = 1 / config.updaterate
        self.alpha = config.pllalpha
        self.events = []
        self.updates = []
        self.medianshift = None

    def bg(self):
        mark = time.time()
        positionindex = 0
        while not self.quit:
            positionindex += 1
            positiontime = self.getpositiontime(mark, positionindex)
            sleeptime = positiontime - time.time()
            if sleeptime > 0:
                time.sleep(sleeptime)
            self.closeupdate()

    def getpositiontime(self, mark, positionindex):
        positiontime = mark + positionindex * self.updateperiod
        if self.medianshift is not None:
            positiontime += self.medianshift
        return positiontime

    def event(self, event, eventtime = None):
        if eventtime is None:
            eventtime = time.time()
        self.events.append((eventtime, event))

    def closeupdate(self, positiontime = None):
        if positiontime is None:
            positiontime = time.time()
        events = self.take(self.events)
        self.updates.append([e for _, e in events])
        # Now update the medianshift, only taking into account events in the context period:
        prevpositiontime = positiontime - self.updateperiod
        targettime = positiontime - self.updateperiod / 2
        shifts = []
        for etime, _ in events:
            if prevpositiontime < etime and etime <= positiontime:
                shifts.append((0 if self.medianshift is None else self.medianshift) + etime - targettime)
        if shifts:
            n = len(shifts)
            if n & 1: # Odd.
                medianshift = shifts[(n - 1) // 2]
            else:
                medianshift = (shifts[n // 2 - 1] + shifts[n // 2]) / 2
            if self.medianshift is None:
                self.medianshift = medianshift
            else:
                self.medianshift = self.alpha * medianshift + (1 - self.alpha) * self.medianshift

    def takeupdate(self):
        update, = self.take(self.updates) # FIXME: Won't always be the case.
        return update
