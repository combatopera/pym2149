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
from const import clientname
from di import types
from config import Config
import alsaseq

class ChannelMessage:

  def __init__(self, midi, event):
    self.midichan = midi.chanbase + event[0]

class NoteOnOff(ChannelMessage):

  def __init__(self, midi, event):
    ChannelMessage.__init__(self, midi, event)
    self.midinote = event[1]
    self.vel = event[2]

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
    self.bend = event[5] # In [-0x2000, 0x2000).

  def __call__(self, channels):
    return channels.pitchbend(self.midichan, self.bend)

  def __str__(self):
    return "B %2d %5d" % (self.midichan, self.bend)

class ProgramChange(ChannelMessage):

  def __init__(self, midi, event):
    ChannelMessage.__init__(self, midi, event)
    self.program = midi.programbase + event[5]

  def __call__(self, channels):
    return channels.programchange(self.midichan, self.program)

  def __str__(self):
    return "P %2d %3d" % (self.midichan, self.program)

class Midi:

  classes = {
    alsaseq.SND_SEQ_EVENT_NOTEON: NoteOn,
    alsaseq.SND_SEQ_EVENT_NOTEOFF: NoteOff,
    alsaseq.SND_SEQ_EVENT_PITCHBEND: PitchBend,
    alsaseq.SND_SEQ_EVENT_PGMCHANGE: ProgramChange,
  }

  @types(Config)
  def __init__(self, config):
    self.chanbase = config.midichannelbase
    self.programbase = config.midiprogrambase
    alsaseq.client(clientname, 1, 0, False)

  def iterevents(self):
    while alsaseq.inputpending():
      type, _, _, _, _, _, _, data = alsaseq.input()
      cls = self.classes.get(type)
      if cls is not None:
        yield cls(self, data)
