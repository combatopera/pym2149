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

class Window:

    def __init__(self, maxspeed):
        self.shapesize = 2 * maxspeed + 1
        self.windowsize = 2 * maxspeed + 1

    def apply(self, data):
        return data[:self.windowsize]

class Shape:

    def __init__(self, window, speed):
        def g():
            for i in xrange(2*speed+1):
                yield 0 if i % speed else 1
        self.shape = np.fromiter(g(), dtype = np.int32)
        self.window = window
        self.speed = speed

    def getscore(self, v):
        return max(np.correlate(self.shape, v[:self.speed*3]))

class SpeedDetector:

    def __init__(self, maxspeed, callback = defaultcallback):
        window = Window(maxspeed)
        self.shapes = [Shape(window, speed) for speed in xrange(1, maxspeed + 1)]
        #for shape in self.shapes: print ''.join(chr(ord('0') + x) if x else '.' for x in shape.shape)
        self.history = np.zeros(maxspeed*3, dtype = np.int32)
        self.speed = None
        self.callback = callback

    def __call__(self, eventcount):
        self.history[1:] = self.history[:-1] # Lose the oldest value.
        self.history[0] = eventcount # New newest value.
        bestscore = -1 # Min legit score is 0.
        scores = []
        #print ''.join(chr(ord('0') + x) if x else '.' for x in self.history)
        scores=[(shape.getscore(self.history), shape.speed) for shape in self.shapes]
        scores.sort()
        bestscore,bestspeed=scores[-1]
        #print ' '.join("%.3f=%s"%s for s in scores),
        accept=scores[-1][0] >= scores[-2][0]*1.1
        #if accept:
        #    print 'OK'
        #else:
        #    print
        if bestspeed != self.speed and accept:
            oldspeed = self.speed
            self.speed = bestspeed
            self.callback(oldspeed, self.speed)
