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


from .const import clientname
from diapyr import types
from .iface import Config, Stream, Chip
from .pll import PLL
from .bg import SimpleBackground, MainBackground
from .channels import Channels
from .minblep import MinBleps
from .timer import Timer
from .util import EMA
from .speed import SpeedDetector
from .native import calsa
import logging, time

log = logging.getLogger(__name__)

class MidiSchedule:

    maxdelay = .01
    targetlatency = .01 # Conservative?

    def __init__(self, updaterate, skipenabled):
        self.period = 1 / updaterate
        self.taketimeema = EMA(.1, time.time())
        self.skipenabled = skipenabled

    def awaittaketime(self):
        skipped = 0
        while True:
            now = time.time()
            if now < self.taketimeema.value:
                time.sleep(self.taketimeema.value - now)
            elif self.skipenabled and now > self.taketimeema.value + self.maxdelay:
                # Forget sync with current update, try the next one:
                self.taketimeema.value += self.period
                skipped += 1
            else: # We're in the [0, maxdelay] window (or late if skip disabled).
                break
        if skipped:
            log.warn("Skipped sync with %s updates.", skipped)
        return now

    def step(self, idealtaketime):
        # TODO: Instead of EMA, improve sync with PLL.
        self.taketimeema.value += self.period
        self.taketimeema(idealtaketime + self.targetlatency)

class ChannelMessage:

    def __init__(self, config, event):
        self.midichan = config.midichannelbase + event.channel

class ChannelStateMessage(ChannelMessage): pass

class NoteOnOff(ChannelMessage):

    def __init__(self, config, event):
        ChannelMessage.__init__(self, config, event)
        self.midinote = event.note
        self.vel = event.velocity

    def __str__(self):
        return "%s %2d %3d %3d" % (self.char, self.midichan, self.midinote, self.vel)

class NoteOn(NoteOnOff):

    char = 'I'

    def __call__(self, channels):
        return channels.noteon(self.midichan, self.midinote, self.vel)

class NoteOff(NoteOnOff):

    char = 'O'

    def __call__(self, channels):
        return channels.noteoff(self.midichan, self.midinote, self.vel)

class PitchBend(ChannelStateMessage):

    def __init__(self, config, event):
        ChannelStateMessage.__init__(self, config, event)
        self.bend = event.value # In [-0x2000, 0x2000).

    def __call__(self, channels):
        return channels.pitchbend(self.midichan, self.bend)

    def __str__(self):
        return "B %2d %5d" % (self.midichan, self.bend)

class ProgramChange(ChannelStateMessage):

    def __init__(self, config, event):
        ChannelStateMessage.__init__(self, config, event)
        self.program = config.midiprogrambase + event.value

    def __call__(self, channels):
        return channels.programchange(self.midichan, self.program)

    def __str__(self):
        return "P %2d %3d" % (self.midichan, self.program)

class ControlChange(ChannelStateMessage):

    def __init__(self, config, event):
        ChannelStateMessage.__init__(self, config, event)
        self.controller = event.param
        self.value = event.value

    def __call__(self, channels):
        return channels.controlchange(self.midichan, self.controller, self.value)

    def __str__(self):
        return "C %2d %3d %3d" % (self.midichan, self.controller, self.value)

class MidiListen(SimpleBackground):

    classes = {
        calsa.SND_SEQ_EVENT_NOTEON: NoteOn,
        calsa.SND_SEQ_EVENT_NOTEOFF: NoteOff,
        calsa.SND_SEQ_EVENT_PITCHBEND: PitchBend,
        calsa.SND_SEQ_EVENT_PGMCHANGE: ProgramChange,
        calsa.SND_SEQ_EVENT_CONTROLLER: ControlChange,
    }

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.pllignoremidichans = set(config.performancechannels)
        log.info("MIDI channels not significant for PLL: {%s}", ', '.join(str(c) for c in sorted(self.pllignoremidichans)))
        self.config = config
        self.pll = pll

    def start(self):
        SimpleBackground.start(self, self.bg, calsa.Client(clientname, "%s IN" % clientname))

    def bg(self, client):
        while not self.quit:
            event = client.event_input()
            if event is not None:
                eventobj = self.classes[event.type](self.config, event)
                self.pll.event(event.time, eventobj, eventobj.midichan not in self.pllignoremidichans)

class EventPump(MainBackground):

    @types(Config, Channels, MinBleps, Stream, Chip, Timer, PLL)
    def __init__(self, config, channels, minbleps, stream, chip, timer, pll):
        MainBackground.__init__(self, config)
        self.updaterate = config.updaterate
        self.performancemidichans = set(config.performancechannels)
        self.skipenabled = config.midiskipenabled
        self.speeddetector = SpeedDetector(10) if config.speeddetector else lambda eventcount: None
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
                if event.midichan not in self.performancemidichans:
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
            for noteevents in chanandnotetoevents.values():
                if NoteOff == noteevents[-1].__class__:
                    sortedevents.extend(noteevents)
            # Then all notes that end up on:
            for noteevents in chanandnotetoevents.values():
                if NoteOn == noteevents[-1].__class__:
                    sortedevents.extend(noteevents)
            for event in sortedevents:
                log.debug("%.6f %s @ %s -> %s", event.offset, event, timecode, event(self.channels))
            self.channels.updateall()
            for block in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(block)
            self.channels.closeframe()
        self.stream.flush()
