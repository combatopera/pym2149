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
import logging, numpy as np
from collections import namedtuple
from pyrbo import turbo
from const import u4

log = logging.getLogger(__name__)

def defaultcallback(oldspeedornone, speed, phase, clarity):
    if oldspeedornone is None:
        log.info("Speed detected: %s", speed)
    else:
        log.warn("Speed was %s but is now: %s", oldspeedornone, speed)

kernelperiods = 2
dtype = np.int32 # Must be signed.
minclarity = 1.1

ScoreSpeedPhase = namedtuple('ScoreSpeedPhase', 'score speed phase')

@turbo(kernel = [dtype], kernelsize = u4, history = [dtype], maxphase = u4, s = dtype, score = dtype, i = u4, j = u4, p = u4, phase = u4)
def correlate(kernel, kernelsize, history, maxphase):
    phase = 0
    score = 0
    j = maxphase
    for i in xrange(kernelsize):
        score += kernel[i] * history[j]
        j += 1
    for p in xrange(1, maxphase + 1):
        s = 0
        j = maxphase - p
        for i in xrange(kernelsize):
            s += kernel[i] * history[j]
            j += 1
        if s > score:
            phase = p
            score = s
    return phase, score

class Shape:

    def __init__(self, speed):
        self.kernelsize = kernelperiods * speed + 1
        def g():
            for i in xrange(self.kernelsize):
                yield -1 if i % speed else 1
        self.kernel = np.fromiter(g(), dtype = dtype)
        self.speed = speed

    def bestscorephase(self, history, index):
        phase, score = correlate(self.kernel, self.kernelsize, history, self.speed - 1)
        return ScoreSpeedPhase(score, self.speed, (index + phase + 1) % self.speed)

class SpeedDetector:

    def __init__(self, maxspeed, callback = defaultcallback):
        self.shapes = [Shape(speed) for speed in xrange(1, maxspeed + 1)]
        self.history = np.zeros(maxspeed * (kernelperiods + 1), dtype = dtype)
        self.speedphase = None
        self.index = 0
        self.callback = callback

    def __call__(self, eventcount):
        self.history[1:] = self.history[:-1] # Lose the oldest value.
        self.history[0] = eventcount # New newest value.
        scorespeedphasetuples = sorted(shape.bestscorephase(self.history, self.index) for shape in self.shapes)
        self.index += 1
        best = scorespeedphasetuples[-1]
        if scorespeedphasetuples[-2].score:
            clarity = scorespeedphasetuples[-1].score / scorespeedphasetuples[-2].score
            if clarity >= minclarity and (best.speed, best.phase) != self.speedphase:
                oldspeedphase = self.speedphase
                self.speedphase = best.speed, best.phase
                self.callback(oldspeedphase, best.speed, best.phase, clarity)
