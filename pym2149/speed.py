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
from collections import namedtuple

log = logging.getLogger(__name__)

def defaultcallback(oldspeedornone, speed):
    if oldspeedornone is None:
        log.info("Speed detected: %s", speed)
    else:
        log.warn("Speed was %s but is now: %s", oldspeedornone, speed)

kernelperiods = 2
dtype = np.int32 # Must be signed.
clarity = 1.1

ScoreSpeedPhase = namedtuple('ScoreSpeedPhase', 'score speed phase')

class Shape:

    def __init__(self, speed):
        def g():
            for i in xrange(kernelperiods * speed + 1):
                yield -1 if i % speed else 1
        self.kernel = np.fromiter(g(), dtype = dtype)
        self.window = speed * (kernelperiods + 1)
        self.speed = speed

    def bestscorephase(self, history, index):
        score, phase = max((score, phase) for phase, score in enumerate(np.correlate(self.kernel, history[:self.window])))
        return ScoreSpeedPhase(score, self.speed, (index + phase + 1) % self.speed)

class SpeedDetector:

    def __init__(self, maxspeed, callback = defaultcallback):
        self.shapes = [Shape(speed) for speed in xrange(1, maxspeed + 1)]
        self.history = np.zeros(maxspeed * (kernelperiods + 1), dtype = dtype)
        self.speed = None
        self.index = 0
        self.callback = callback

    def __call__(self, eventcount):
        self.history[1:] = self.history[:-1] # Lose the oldest value.
        self.history[0] = eventcount # New newest value.
        scorespeedphasetuples = sorted(shape.bestscorephase(self.history, self.index) for shape in self.shapes)
        self.index += 1
        newspeed = scorespeedphasetuples[-1].speed, scorespeedphasetuples[-1].phase
        accept = scorespeedphasetuples[-1].score and scorespeedphasetuples[-1].score >= scorespeedphasetuples[-2].score * clarity
        if newspeed != self.speed and accept:
            oldspeed = self.speed
            self.speed = newspeed
            self.callback(oldspeed, self.speed)
