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
import alsaseq, multiprocessing, multiprocessing.queues

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

class ControlChange(ChannelMessage):

  def __init__(self, midi, event):
    ChannelMessage.__init__(self, midi, event)
    self.controller = event[4]
    self.value = event[5]

  def __call__(self, channels):
    return channels.controlchange(self.midichan, self.controller, self.value)

  def __str__(self):
    return "C %2d %3d %3d" % (self.midichan, self.controller, self.value)

class Midi:

  classes = {
    alsaseq.SND_SEQ_EVENT_NOTEON: NoteOn,
    alsaseq.SND_SEQ_EVENT_NOTEOFF: NoteOff,
    alsaseq.SND_SEQ_EVENT_PITCHBEND: PitchBend,
    alsaseq.SND_SEQ_EVENT_PGMCHANGE: ProgramChange,
    alsaseq.SND_SEQ_EVENT_CONTROLLER: ControlChange,
  }

  @types(Config, PLL)
  def __init__(self, config, pll):
    self.chanbase = config.midichannelbase
    self.programbase = config.midiprogrambase
    self.pll = pll

  def start(self):
    self.eventqueue = multiprocessing.queues.SimpleQueue()
    # XXX: Is it actually necessary to pass the queue?
    self.process = multiprocessing.Process(target = self, args = (self.eventqueue,))
    self.process.start()

  def __call__(self, eventqueue):
    alsaseq.client(clientname, 1, 0, False)
    while True:
      event = alsaseq.input() # Can't hold the GIL while blocking here, which is why we use multiprocessing.
      cls = self.classes.get(event[0])
      if cls is not None:
        eventqueue.put(cls(self, event[7]))

  def getevents(self):
    events = []
    while not self.eventqueue.empty():
      events.append(self.eventqueue.get())
    return events

  def stop(self):
    self.process.terminate() # A bit heavy-handed.
    self.process.join()
