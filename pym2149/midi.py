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

import pypm, sys

class Midi:

  def __enter__(self):
    pypm.Initialize()
    return self

  def selectdevice(self):
    for index in xrange(pypm.CountDevices()):
      info = pypm.GetDeviceInfo(index)
      if info[2]: # It's an input device.
        print >> sys.stderr, "%2d) %s" % (index, info[1])
    print >> sys.stderr, 'Index? ',
    return Device(int(raw_input())) # Apparently int ignores whitespace.

  def __exit__(self, *args):
    pypm.Terminate()

class Device:

  def __init__(self, index):
    self.index = index

  def start(self):
    self.input = pypm.Input(self.index) # Deferring this helps avoid PortMidi buffer overflow.

  def iterevents(self):
    while self.input.Poll():
      event, = self.input.Read(1)
      event, _ = event # XXX: What is the second field?
      kind = event[0] & 0xf0
      if 0x90 == kind:
        yield NoteOn(event)
      elif 0x80 == kind:
        yield NoteOff(event)

class NoteOnOff:

  def __init__(self, event):
    self.midichan = 1 + (event[0] & 0x0f)
    self.note = event[1]

  def __str__(self):
    return "%s %2d %3d" % (self.char, self.midichan, self.note)

class NoteOn(NoteOnOff):

  char = 'I'

  def __call__(self, channels, frame):
    return channels.noteon(frame, self.midichan, self.note)

class NoteOff(NoteOnOff):

  char = 'O'

  def __call__(self, channels, frame):
    return channels.noteoff(frame, self.midichan, self.note)

class Patch:

  def __init__(self, chip, index):
    self.chip = chip
    self.index = index

  def noteon(self, pitch): pass

  def noteonframe(self, frame): pass

  def noteoff(self): pass

  def noteoffframe(self, frame): pass

class DefaultPatch(Patch):

  def noteon(self, pitch):
    self.chip.toneperiods[self.index].value = pitch.freq().toneperiod(self.chip.nominalclock())
    self.chip.toneflags[self.index].value = True
    self.chip.fixedlevels[self.index].value = 15

  def noteoffframe(self, frame):
    self.chip.fixedlevels[self.index].value = max(14 - frame, 0)
