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

import logging, numpy as np

log = logging.getLogger(__name__)

def defaultcallback(oldspeedornone, speed):
    if oldspeedornone is None:
        log.info("Speed detected: %s", speed)
    else:
        log.warn("Speed was %s but is now: %s", oldspeedornone, speed)

periods = 2
dtype = np.uint8
clarity = 1.2

class Shape:

    def __init__(self, speed):
        def g():
            for i in xrange(periods * speed + 1):
                yield 0 if i % speed else 1
        self.shape = np.fromiter(g(), dtype = dtype)
        self.speed = speed

    def getscore(self, v):
        return max((score, self.speed - 1 - phase) for phase, score in enumerate(np.correlate(self.shape, v[:self.speed * (periods + 1)])))

class SpeedDetector:

    def __init__(self, maxspeed, callback = defaultcallback):
        self.shapes = [Shape(speed) for speed in xrange(1, maxspeed + 1)]
        #for shape in self.shapes: print ''.join(chr(ord('0') + x) if x else '.' for x in shape.shape)
        self.history = np.zeros(maxspeed * (periods + 1), dtype = dtype)
        self.speed = None
        self.index = 0
        self.callback = callback

    def __call__(self, eventcount):
        self.history[1:] = self.history[:-1] # Lose the oldest value.
        self.history[0] = eventcount # New newest value.
        #print ''.join(chr(ord('0') + x) if x else '.' for x in self.history)
        scores = sorted((shape.getscore(self.history), shape.speed) for shape in self.shapes)
        scores = [(score, (speed, (self.index - phase) % speed)) for (score, phase), speed in scores]
        newspeed = scores[-1][1]
        #print self.history,newspeed
        #print ' '.join("%.3f=%s"%s for s in scores),
        accept = scores[-1][0] and scores[-1][0] >= scores[-2][0] * clarity
        #if accept:
        #    print 'OK'
        #else:
        #    print
        self.index += 1
        if newspeed != self.speed and accept:
            print self.history, scores[-3:]
            oldspeed = self.speed
            self.speed = newspeed
            self.callback(oldspeed, self.speed)
