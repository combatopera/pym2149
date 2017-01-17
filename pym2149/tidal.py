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

from diapyr import types
from iface import Config, Stream, Chip
from pll import PLL
from bg import SimpleBackground, MainBackground
from channels import Channels
from minblep import MinBleps
from timer import Timer
from speed import SpeedDetector
from midi import MidiSchedule
import logging, time

log = logging.getLogger(__name__)

class TidalClient:

    def __init__(self):
        self.open = True

    def read(self):
        while self.open:
            time.sleep(1)

    def interrupt(self):
        self.open = False

class TidalListen(SimpleBackground):

    @types(PLL)
    def __init__(self, pll):
        self.pll = pll

    def start(self):
        SimpleBackground.start(self, self.bg, TidalClient())

    def bg(self, client):
        while not self.quit:
            event = client.read()
            if event is not None:
                self.pll.event(event.time, event, True)

class TidalPump(MainBackground):

    @types(Config, TidalListen, Channels, MinBleps, Stream, Chip, Timer, PLL)
    def __init__(self, config, midi, channels, minbleps, stream, chip, timer, pll):
        MainBackground.__init__(self, config)
        self.updaterate = config.updaterate
        self.skipenabled = config.midiskipenabled # Allow False in case we want to render.
        self.speeddetector = SpeedDetector(10) if config.speeddetector else lambda eventcount: None
        self.midi = midi
        self.channels = channels
        self.minbleps = minbleps
        self.stream = stream
        self.chip = chip
        self.timer = timer
        self.pll = pll

    def __call__(self):
        schedule = MidiSchedule(self.updaterate, self.skipenabled)
        while not self.quit:
            update = self.pll.takeupdateimpl(schedule.awaittaketime())
            schedule.step(update.idealtaketime)
            scheduledevents = 0
            for event in update.events:
                scheduledevents += 1
            self.speeddetector(scheduledevents)
            timecode = self.channels.frameindex
            if self.speeddetector.speedphase is not None:
                speed = self.speeddetector.speedphase[0]
                timecode = "%s*%s+%s" % (timecode // speed, speed, timecode % speed)
            chanandnotetoevents = {}
            for event in update.events:
                if isinstance(event, NoteOnOff):
                    try:
                        chanandnotetoevents[event.midichan, event.midinote].append(event)
                    except KeyError:
                        chanandnotetoevents[event.midichan, event.midinote] = [event]
            # Apply all channel state events first:
            sortedevents = [event for event in update.events if isinstance(event, ChannelStateMessage)]
            # Then all notes that end up off:
            for noteevents in chanandnotetoevents.itervalues():
                if NoteOff == noteevents[-1].__class__:
                    sortedevents.extend(noteevents)
            # Then all notes that end up on:
            for noteevents in chanandnotetoevents.itervalues():
                if NoteOn == noteevents[-1].__class__:
                    sortedevents.extend(noteevents)
            for event in sortedevents:
                log.debug("%.6f %s @ %s -> %s", event.offset, event, timecode, event(self.channels))
            self.channels.updateall()
            for block in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(block)
            self.channels.closeframe()
        self.stream.flush()
