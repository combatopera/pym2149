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

from .const import clientname
from .iface import Config, Stream, Timer
from .pll import PLL
from .channels import Channels
from .util import EMA
from .speed import SpeedDetector
from .native import calsa
from diapyr import types
from diapyr.util import singleton
from splut.bg import MainBackground, SimpleBackground
import logging, time

log = logging.getLogger(__name__)

class UpdateSchedule:

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
            log.warning("Skipped sync with %s updates.", skipped)
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

    @staticmethod
    def formatchipchans(chipchans):
        if chipchans is not None:
            return ''.join(chr(ord('A') + chipchan) for chipchan in chipchans)

    def __init__(self, config, event):
        super().__init__(config, event)
        self.midinote = event.note
        self.vel = event.velocity

    def __str__(self):
        return "%s %2s %3s %3s" % (self.char, self.midichan, self.midinote, self.vel)

class NoteOn(NoteOnOff):

    char = 'I'

    def __call__(self, channels):
        return self.formatchipchans(channels.noteon(self.midichan, self.midinote, self.vel))

class NoteOff(NoteOnOff):

    char = 'O'

    def __call__(self, channels):
        return self.formatchipchans(channels.noteoff(self.midichan, self.midinote, self.vel))

class PitchBend(ChannelStateMessage):

    def __init__(self, config, event):
        super().__init__(config, event)
        self.bend = event.value # In [-0x2000, 0x2000).

    def __call__(self, channels):
        return channels.pitchbend(self.midichan, self.bend)

    def __str__(self):
        return "B %2d %5d" % (self.midichan, self.bend)

class ProgramChange(ChannelStateMessage):

    def __init__(self, config, event):
        super().__init__(config, event)
        self.program = config.midiprogrambase + event.value

    def __call__(self, channels):
        return channels.programchange(self.midichan, self.program)

    def __str__(self):
        return "P %2s %3s" % (self.midichan, self.program)

class ControlChange(ChannelStateMessage):

    def __init__(self, config, event):
        super().__init__(config, event)
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
        super().__init__(config.profile)
        self.pllignoremidichans = set(config.performancechannels)
        log.info("MIDI channels not significant for PLL: {%s}", ', '.join(str(c) for c in sorted(self.pllignoremidichans)))
        self.config = config
        self.pll = pll

    def start(self):
        super().start(self.bg, calsa.Client(clientname.encode(), ("%s IN" % clientname).encode()))

    def bg(self, client):
        while not self.quit:
            event = client.event_input()
            if event is not None:
                eventobj = self.classes[event.type](self.config, event)
                self.pll.event(event.time, eventobj, eventobj.midichan not in self.pllignoremidichans)

@singleton
class NullSpeedDetector:

    speedphase = None

    def __call__(self, eventcount): pass

class EventPump(MainBackground):

    @types(Config, Channels, Stream, Timer, PLL)
    def __init__(self, config, channels, stream, timer, pll):
        super().__init__(config)
        self.updaterate = config.updaterate
        self.performancemidichans = set(config.performancechannels)
        self.skipenabled = config.inputskipenabled
        self.speeddetector = SpeedDetector(10) if config.speeddetector else NullSpeedDetector
        self.channels = channels
        self.stream = stream
        self.timer = timer
        self.pll = pll

    def __call__(self):
        schedule = UpdateSchedule(self.updaterate, self.skipenabled)
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
            sortedevents = [event for event in update.events if isinstance(event, ChannelStateMessage)] # XXX: Before off?
            # Then all notes that end up off:
            for noteevents in chanandnotetoevents.values():
                if NoteOff == type(noteevents[-1]): # FIXME: May be simulated NoteOff for previous NoteOn.
                    sortedevents.extend(noteevents)
            # Then all notes that end up on:
            for noteevents in chanandnotetoevents.values():
                if NoteOn == type(noteevents[-1]):
                    sortedevents.extend(noteevents)
            # Any custom events:
            sortedevents.extend(event for event in update.events if not isinstance(event, ChannelMessage)) # XXX: Retire?
            format = "%s %.6f %s%s"
            for event in sortedevents:
                try:
                    response = event(self.channels)
                    log.debug(format, timecode, event.offset, event, '' if response is None else " -> %s" % response)
                except Exception:
                    log.exception(format, timecode, event.offset, event, '')
            self.channels.updateall()
            for block in self.timer.blocksforperiod(self.updaterate):
                self.stream.call(block)
            self.channels.closeframe()
        self.stream.flush()
