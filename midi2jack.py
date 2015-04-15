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
from pym2149.jackclient import JackClient, configure
from pym2149.nod import Block
from pym2149.midi import Midi, SpeedDetector
from pym2149.config import getprocessconfig
from pym2149.channels import Channels
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream, Config
from pym2149.minblep import MinBleps
from pym2149.di import types
from pym2149.util import awaitinterrupt
from pym2149.timer import Timer, SimpleTimer
from pym2149.ym2149 import ClockInfo
from pym2149.bg import MainBackground
from pym2149.pll import PLL
from midi2wav import StreamReady

log = logging.getLogger(__name__)

class SyncTimer(SimpleTimer):

    @types(Stream, MinBleps, ClockInfo)
    def __init__(self, stream, minbleps, clockinfo):
        self.naiverate = clockinfo.implclock
        SimpleTimer.__init__(self, self.naiverate)
        self.buffersize = stream.getbuffersize()
        self.naivex = 0
        self.bufferx = 0
        self.minbleps = minbleps

    def blocksforperiod(self, refreshrate):
        wholeperiodblock, = SimpleTimer.blocksforperiod(self, refreshrate)
        naiveN = wholeperiodblock.framecount
        while naiveN:
            naiven = min(naiveN, self.minbleps.getminnaiven(self.naivex, self.buffersize - self.bufferx))
            yield Block(naiven)
            self.bufferx = (self.bufferx + self.minbleps.getoutcount(self.naivex, naiven)) % self.buffersize
            self.naivex = (self.naivex + naiven) % self.naiverate
            naiveN -= naiven

class MidiPump(MainBackground):

    @types(Config, Midi, Channels, MinBleps, Stream, Chip, Timer)
    def __init__(self, config, midi, channels, minbleps, stream, chip, timer):
        MainBackground.__init__(self, config)
        self.updaterate = config.updaterate
        self.midi = midi
        self.channels = channels
        self.minbleps = minbleps
        self.stream = stream
        self.chip = chip
        self.timer = timer

    def __call__(self):
        streamready = StreamReady(self.updaterate)
        speeddetector = SpeedDetector()
        while not self.quit:
            streamready.await()
            events = self.midi.getevents()
            speeddetector(bool(events))
            # TODO: For best mediation, advance note-off events that would cause instantaneous polyphony.
            for offset, event in events:
                log.debug("%.6f %s @ %s -> %s", offset, event, self.channels.frameindex, event(self.channels))
            self.channels.updateall()
            for block in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(block)
            self.channels.closeframe()

def main():
    config = getprocessconfig()
    di = createdi(config)
    di.add(PLL)
    di.add(Midi)
    di.add(JackClient)
    di.start()
    try:
        configure(di)
        di.add(Channels)
        di.start()
        log.info(di(Channels))
        stream = di(Stream)
        log.debug("JACK block size: %s or %.3f seconds", stream.getbuffersize(), stream.getbuffersize() / config.outputrate)
        di.add(SyncTimer)
        di.add(MidiPump)
        di.start()
        awaitinterrupt(config)
    finally:
        di.stop()

if '__main__' == __name__:
    main()
