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
import time

class PLL:

    @types(Config)
    def __init__(self, config):
        self.updateperiod = 1 / config.updaterate
        self.targetpos = config.plltargetpos
        self.alpha = config.pllalpha

    def start(self):
        self.events = []
        self.updates = []
        self.medianshift = None
        self.mark = time.time()
        self.windowindex = 0
        self.nextwindow()

    def stop(self):
        pass

    def nextwindow(self):
        self.windowindex += 1
        self.exclusivewindowend = self.mark + self.windowindex * self.updateperiod
        if self.medianshift is not None:
            self.exclusivewindowend += self.medianshift

    def event(self, eventtime, event):
        self.events.append((eventtime, event))

    def closeupdate(self):
        inclusivewindowstart = self.exclusivewindowend - self.updateperiod
        targettime = inclusivewindowstart + self.updateperiod * self.targetpos
        shifts = []
        i = 0
        preshift = 0 if self.medianshift is None else self.medianshift
        for eventtime, _ in self.events:
            if eventtime >= self.exclusivewindowend:
                break
            if eventtime >= inclusivewindowstart:
                shifts.append(preshift + eventtime - targettime)
            i += 1
        self.updates.append([(eventtime - inclusivewindowstart, event) for eventtime, event in self.events[:i]])
        del self.events[:i]
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
        self.nextwindow()

    def takeupdate(self):
        return self.takeupdateimpl(time.time())

    def takeupdateimpl(self, now):
        while now >= self.exclusivewindowend: # No more events can qualify for this window.
            self.closeupdate()
        update = sum(self.updates, [])
        del self.updates[:]
        return update
