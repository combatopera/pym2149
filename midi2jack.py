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
from pym2149.jackclient import JackClient
from pym2149.nod import Block
from config import getprocessconfig
import pypm, sys

log = logging.getLogger(__name__)

class Midi:

  def __enter__(self):
    pypm.Initialize()
    return self

  def selectdevice(self):
    for i in xrange(pypm.CountDevices()):
      info = pypm.GetDeviceInfo(i)
      if info[2]: # It's an input device.
        print >> sys.stderr, "%2d) %s" % (i, info[1])
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

class Channel:

  def __init__(self, chipindex):
    self.on = None
    self.chipindex = chipindex

  def noteon(self, frame, note):
    self.on = True
    self.note = note
    self.onframe = frame

  def noteoff(self, frame):
    self.on = False
    self.offframe = frame

  def __str__(self):
    return chr(ord('A') + self.chipindex)

class Channels:

  def __init__(self, config):
    self.midichantochannels = {}
    for chipindex, midichan in enumerate(config.midichannels):
      channel = Channel(chipindex)
      try:
        self.midichantochannels[midichan].append(channel)
      except KeyError:
        self.midichantochannels[midichan] = [channel]

  def noteon(self, frame, midichan, note):
    try:
      channels = self.midichantochannels[midichan]
    except KeyError:
      return
    # Use a blank channel if there is one:
    for c in channels:
      if c.on is None:
        c.noteon(frame, note)
        return c
    # If any channels are in the off state, use the one that has been for longest:
    oldest = None
    for c in channels:
      if not c.on and (oldest is None or c.offframe < oldest.offframe):
        oldest = c
    if oldest is not None:
      oldest.noteon(frame, note)
      return oldest
    # They're all in the on state, use the one that has been for longest:
    for c in channels:
      if oldest is None or c.onframe < oldest.onframe:
        oldest = c
    oldest.noteon(frame, note)
    return oldest

  def noteoff(self, frame, midichan, note):
    try:
      channels = self.midichantochannels[midichan]
    except KeyError:
      return
    # Find the matching channel that has been in the on state for longest:
    oldest = None
    for c in channels:
      if c.on and note == c.note and (oldest is None or c.onframe < oldest.onframe):
        oldest = c
    if oldest is not None:
      oldest.noteoff(frame)
      return oldest

  def __str__(self):
    return ', '.join("%s -> %s" % (midichan, ''.join(map(str, channels))) for midichan, channels in sorted(self.midichantochannels.iteritems()))

def main():
  config = getprocessconfig()
  channels = Channels(config)
  log.info(channels)
  with Midi() as midi:
    device = midi.selectdevice()
    with JackClient(config) as jackclient:
      chip, stream = jackclient.newchipandstream(None)
      try:
        log.debug("JACK block size: %s or %.3f seconds", stream.size, stream.size / config.getoutputrate())
        minbleps = stream.wavs[0].minbleps
        naivex = 0
        frame = 0
        device.start()
        log.debug('MIDI listener started.')
        while True:
          for event in device.iterevents():
            log.debug("%s @ %s -> %s", event, frame, event(channels, frame))
          # Make min amount of chip data to get one JACK block:
          naiven = minbleps.getminnaiven(naivex, stream.size)
          stream.call(Block(naiven))
          naivex = (naivex + naiven) % chip.clock
          frame += 1
      finally:
        stream.close()

if '__main__' == __name__:
  main()
