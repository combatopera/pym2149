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

from __future__ import division
from pym2149.initlogging import logging
from pym2149.out import configure
from pym2149.midi import Midi
from pym2149.config import getprocessconfig
from pym2149.channels import Channels
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream, Config
from pym2149.minblep import MinBleps
from pym2149.di import types
from pym2149.util import awaitinterrupt
from pym2149.timer import Timer
from pym2149.bg import Background
from ymplayer import SimpleChipTimer
import time

log = logging.getLogger(__name__)

class StreamReady:

    def __init__(self, updaterate):
        self.period = 1 / updaterate
        self.readytime = time.time()

    def await(self):
        sleeptime = self.readytime - time.time()
        if sleeptime > 0:
            time.sleep(sleeptime)
        self.readytime += self.period

class MidiPump(Background):

    @types(Config, Midi, Channels, MinBleps, Stream, Chip, Timer)
    def __init__(self, config, midi, channels, minbleps, stream, chip, timer):
        Background.__init__(self, config)
        self.updaterate = config.updaterate
        self.midi = midi
        self.channels = channels
        self.minbleps = minbleps
        self.stream = stream
        self.chip = chip
        self.timer = timer

    def __call__(self):
        streamready = StreamReady(self.updaterate)
        while not self.quit:
            for event in self.midi.iterevents():
                log.debug("%s @ %s -> %s", event, self.channels.frameindex, event(self.channels))
            self.channels.updateall()
            streamready.await() # Simulate blocking behaviour of a real device.
            for b in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(b)
            self.channels.closeframe()
        self.stream.flush()

def main():
    config = getprocessconfig('outpath')
    di = createdi(config)
    di.add(Midi)
    configure(di)
    di.start()
    try:
        di.add(Channels)
        channels = di(Channels)
        log.info(channels)
        di.add(SimpleChipTimer) # One block per update.
        di.add(MidiPump)
        di.start()
        awaitinterrupt(config)
    finally:
        di.stop()

if '__main__' == __name__:
    main()
