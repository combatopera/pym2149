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
from jackclient import clientname
import alsaseq

class Midi:

  def __init__(self):
    alsaseq.client(clientname, 1, 0, False)

  def iterevents(self):
    while alsaseq.inputpending():
      type, _, _, _, _, _, _, data = alsaseq.input()
      if alsaseq.SND_SEQ_EVENT_NOTEON == type:
        yield NoteOn(data)
      elif alsaseq.SND_SEQ_EVENT_NOTEOFF == type:
        yield NoteOff(data)

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
