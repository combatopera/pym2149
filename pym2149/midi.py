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

from const import clientname
from di import types
from iface import Config
from pll import PLL
from bg import SimpleBackground
import calsa

class SpeedDetector:

    def __init__(self):
        self.update = 0
        self.lastevent = None
        self.speed = None

    def __call__(self, event):
        if event:
            if self.lastevent is not None:
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

class ChannelMessage:

    def __init__(self, midi, event):
        self.midichan = midi.chanbase + event.channel

class NoteOnOff(ChannelMessage):

    def __init__(self, midi, event):
        ChannelMessage.__init__(self, midi, event)
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

class PitchBend(ChannelMessage):

    def __init__(self, midi, event):
        ChannelMessage.__init__(self, midi, event)
        self.bend = event.value # In [-0x2000, 0x2000).

    def __call__(self, channels):
        return channels.pitchbend(self.midichan, self.bend)

    def __str__(self):
        return "B %2d %5d" % (self.midichan, self.bend)

class ProgramChange(ChannelMessage):

    def __init__(self, midi, event):
        ChannelMessage.__init__(self, midi, event)
        self.program = midi.programbase + event.value

    def __call__(self, channels):
        return channels.programchange(self.midichan, self.program)

    def __str__(self):
        return "P %2d %3d" % (self.midichan, self.program)

class ControlChange(ChannelMessage):

    def __init__(self, midi, event):
        ChannelMessage.__init__(self, midi, event)
        self.controller = event.param
        self.value = event.value

    def __call__(self, channels):
        return channels.controlchange(self.midichan, self.controller, self.value)

    def __str__(self):
        return "C %2d %3d %3d" % (self.midichan, self.controller, self.value)

class Midi(SimpleBackground):

    classes = {
        calsa.SND_SEQ_EVENT_NOTEON: NoteOn,
        calsa.SND_SEQ_EVENT_NOTEOFF: NoteOff,
        calsa.SND_SEQ_EVENT_PITCHBEND: PitchBend,
        calsa.SND_SEQ_EVENT_PGMCHANGE: ProgramChange,
        calsa.SND_SEQ_EVENT_CONTROLLER: ControlChange,
    }

    @types(Config, PLL)
    def __init__(self, config, pll):
        self.chanbase = config.midichannelbase
        self.programbase = config.midiprogrambase
        self.pll = pll

    def bg(self):
        client = calsa.Client(clientname)
        while not self.quit: # FIXME: Prevents app exit if MIDI is quiet.
            event = client.event_input()
            self.pll.event(event.time, self.classes.get(event.type)(self, event))

    def getevents(self):
        return self.pll.takeupdate()
