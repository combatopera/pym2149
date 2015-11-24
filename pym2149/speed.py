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

import logging

log = logging.getLogger(__name__)

class SpeedDetector:

    def __init__(self):
        self.update = 0
        self.lastevent = None
        self.speed = None

    def __call__(self, event):
        if event:
            if self.lastevent is not None:
                # FIXME LATER: When this goes to 1 it can't recover.
                speed = self.update - self.lastevent
                if self.speed is None:
                    log.info("Speed detected: %s", speed)
                    self.speed = speed
                elif speed % self.speed:
                    log.warn("Speed was %s but is now: %s", self.speed, speed)
                    self.speed = speed
                else:
                    pass # Do nothing, multiples of current speed are fine.
            self.lastevent = self.update
        self.update += 1
