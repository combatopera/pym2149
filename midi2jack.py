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
from pym2149.pitch import Pitch
from pym2149.midi import Midi
from config import getprocessconfig

log = logging.getLogger(__name__)

def veltovoladj(vel):
  return (vel - 52) // 24 # TODO: Make configurable.

class Channel:

  def __init__(self, chipindex, chip):
    self.onornone = None
    self.chipindex = chipindex
    self.chip = chip

  def noteon(self, frame, patch, note, vel):
    self.onornone = True
    self.onframe = frame
    self.patch = patch
    self.note = note
    self.vel = vel

  def noteoff(self, frame):
    self.onornone = False
    self.offframe = frame

  def update(self, frame):
    bend = 0 # TODO: Implement bend and other fx.
    if self.onornone:
      f = frame - self.onframe
      if not f:
        # Make it so that the patch only has to switch things on:
        self.chip.flagsoff(self.chipindex)
        self.patch.noteon(Pitch(self.note), veltovoladj(self.vel))
      self.patch.noteonframe(f, bend)
    elif self.onornone is not None: # It's False.
      f = frame - self.offframe
      if not f:
        self.patch.noteoff()
      self.patch.noteoffframe(self.offframe - self.onframe, f, bend)

  def __str__(self):
    return chr(ord('A') + self.chipindex)

class Channels:

  def __init__(self, config, chip):
    self.channels = dict([chr(ord('A') + i), Channel(i, chip)] for i in xrange(chip.channels))
    self.patches = config.patches

  def noteon(self, frame, midichan, note, vel):
    try:
      patchinfo = self.patches[midichan]
    except KeyError:
      return
    channels = [self.channels[c] for c in patchinfo.restrict]
    # Use a blank channel if there is one:
    for c in channels:
      if c.onornone is None:
        c.noteon(frame, patchinfo.patch, note, vel)
        return c
    # If any channels are in the off state, use the one that has been for longest:
    oldest = None
    for c in channels:
      if not c.onornone and (oldest is None or c.offframe < oldest.offframe):
        oldest = c
    if oldest is not None:
      oldest.noteon(frame, patchinfo.patch, note, vel)
      return oldest
    # They're all in the on state, use the one that has been for longest:
    for c in channels:
      if oldest is None or c.onframe < oldest.onframe:
        oldest = c
    oldest.noteon(frame, patchinfo.patch, note, vel)
    return oldest

  def noteoff(self, frame, midichan, note, vel):
    try:
      patchinfo = self.patches[midichan]
    except KeyError:
      return
    channels = [self.channels[c] for c in patchinfo.restrict]
    # Find the matching channel that has been in the on state for longest:
    oldest = None
    for c in channels:
      if c.onornone and note == c.note and (oldest is None or c.onframe < oldest.onframe):
        oldest = c
    if oldest is not None:
      oldest.noteoff(frame)
      return oldest

  def updateall(self, frame):
    for channel in self.channels:
      channel.update(frame)

  def __str__(self):
    return ', '.join("%s -> %s" % entry for entry in sorted(self.patches.iteritems()))

def main():
  config = getprocessconfig()
  midi = Midi()
  with JackClient(config) as jackclient:
      chip, stream = jackclient.newchipandstream(None)
      try:
        channels = Channels(config, chip)
        log.info(channels)
        log.debug("JACK block size: %s or %.3f seconds", stream.size, stream.size / config.getoutputrate())
        minbleps = stream.wavs[0].minbleps
        naivex = 0
        frame = 0
        while True:
          for event in midi.iterevents():
            log.debug("%s @ %s -> %s", event, frame, event(channels, frame))
          channels.updateall(frame)
          # Make min amount of chip data to get one JACK block:
          naiven = minbleps.getminnaiven(naivex, stream.size)
          stream.call(Block(naiven))
          naivex = (naivex + naiven) % chip.clock
          frame += 1
      finally:
        stream.close()

if '__main__' == __name__:
  main()
