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

from .iface import Config
from diapyr import types
from .util import EMA
import time, logging

log = logging.getLogger(__name__)

class Update:

    def __init__(self, events, idealtaketime):
        self.events = events
        self.idealtaketime = idealtaketime

class PLL:

    @types(Config)
    def __init__(self, config):
        self.updateperiod = 1 / config.updaterate
        self.targetpos = float(config.plltargetpos)
        self.medianshiftema = EMA(float(config.pllalpha), None)

    def start(self):
        self.events = []
        self.updates = []
        self.medianshiftema.value = 0
        self.mark = time.time()
        self.windowindex = 0
        self.nextwindow()

    def stop(self):
        pass

    def nextwindow(self):
        self.windowindex += 1
        self.exclusivewindowend = self.mark + self.windowindex * self.updateperiod + self.medianshiftema.value

    def event(self, eventtime, event, significant):
        self.events.append((eventtime, event, significant))

    def closeupdate(self):
        inclusivewindowstart = self.exclusivewindowend - self.updateperiod
        targettime = inclusivewindowstart + self.targetpos
        shifts = []
        i = 0
        for eventtime, _, significant in self.events:
            if eventtime >= self.exclusivewindowend:
                break
            if significant and eventtime >= inclusivewindowstart:
                shifts.append(self.medianshiftema.value + eventtime - targettime)
            # If eventtime < inclusivewindowstart we consume the event without harvesting its shift.
            i += 1
        update = []
        for eventtime, event, _ in self.events[:i]:
            event.offset = eventtime - inclusivewindowstart
            update.append(event)
        self.updates.append(update)
        del self.events[:i]
        if shifts:
            n = len(shifts)
            if n & 1: # Odd.
                medianshift = shifts[(n - 1) // 2]
            else:
                midindex = n // 2
                medianshift = (shifts[midindex - 1] + shifts[midindex]) / 2
            self.medianshiftema(medianshift)
        self.nextwindow()

    def takeupdate(self):
        return self.takeupdateimpl(time.time())

    def takeupdateimpl(self, now):
        while now >= self.exclusivewindowend: # No more events can qualify for this window.
            self.closeupdate()
        copy = self.updates[:]
        n = len(copy)
        del self.updates[:n] # Not actually necessary to use n, as only we call closeupdate.
        if 1 == n:
            update, = copy
        else:
            log.warning("Yielding %s updates as one.", n)
            update = sum(copy, [])
        return Update(update, self.exclusivewindowend)
