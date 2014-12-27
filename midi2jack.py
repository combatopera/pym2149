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
from pym2149.patch import FX
from pym2149.midi import Midi
from config import getprocessconfig

log = logging.getLogger(__name__)

# TODO: Make configurable.
veldatum = 0x60
velpervol = 0x10

def veltovoladj(vel):
  return (vel - veldatum + velpervol // 2) // velpervol

class Channel:

  def __init__(self, chipindex, chip):
    self.onornone = None
    self.chipindex = chipindex
    self.chip = chip
    self.patch = None

  def noteon(self, frame, patch, note, vel, fx):
    self.onornone = True
    self.onframe = frame
    self.patch = patch(self.chip, self.chipindex)
    self.note = note
    self.vel = vel
    self.fx = fx

  def noteoff(self, frame):
    self.onornone = False
    self.offframe = frame

  def update(self, frame):
    if self.onornone:
      f = frame - self.onframe
      if not f:
        self.noteonimpl()
      self.patch.noteonframe(f)
    elif self.onornone is not None: # It's False.
      if self.onframe == self.offframe:
        self.noteonimpl()
      f = frame - self.offframe
      if not f:
        self.patch.noteoff()
      self.patch.noteoffframe(self.offframe - self.onframe, f)

  def noteonimpl(self):
    # Make it so that the patch only has to switch things on:
    self.chip.flagsoff(self.chipindex)
    self.patch.noteon(Pitch(self.note), veltovoladj(self.vel), self.fx)

  def __str__(self):
    return chr(ord('A') + self.chipindex)

class Channels:

  def __init__(self, config, chip):
    self.channels = [Channel(i, chip) for i in xrange(chip.channels)]
    self.patches = config.patches
    self.midichantofx = dict([1 + i, FX()] for i in xrange(16))
    self.midichans = [None] * chip.channels
    self.miditopriority = [list(self.channels) for _ in xrange(16)]
    self.prevtext = None

  def noteon(self, frame, midichan, note, vel):
    try:
      patch = self.patches[midichan]
    except KeyError:
      return
    fx = self.midichantofx[midichan]
    # Use a blank channel if there is one:
    for c in self.miditopriority[midichan]:
      if c.onornone is None:
        return self.noteoninchan(frame, midichan, note, vel, c)
    # If any channels are in the off state, use the one that has been for longest:
    oldest = None
    for c in self.miditopriority[midichan]:
      if not c.onornone and (oldest is None or c.offframe < oldest.offframe):
        oldest = c
    if oldest is not None:
      return self.noteoninchan(frame, midichan, note, vel, oldest)
    # They're all in the on state, use the one that has been for longest:
    for c in self.miditopriority[midichan]:
      if oldest is None or c.onframe < oldest.onframe:
        oldest = c
    return self.noteoninchan(frame, midichan, note, vel, oldest)

  def noteoninchan(self, frame, midichan, note, vel, channel):
    patch = self.patches[midichan]
    fx = self.midichantofx[midichan]
    channel.noteon(frame, patch, note, vel, fx)
    self.midichans[channel.chipindex] = midichan
    self.miditopriority[midichan].remove(channel)
    self.miditopriority[midichan][0:0] = [channel]
    return channel

  def noteoff(self, frame, midichan, note, vel):
    # Find the matching channel that has been in the on state for longest:
    oldest = None
    for c in self.miditopriority[midichan]:
      if c.onornone and note == c.note and (oldest is None or c.onframe < oldest.onframe):
        oldest = c
    if oldest is not None:
      oldest.noteoff(frame)
      return oldest

  def pitchbend(self, frame, midichan, bend):
    self.midichantofx[midichan].bend = bend

  def updateall(self, frame):
    text = ' | '.join("%s@%s" % (c.patch, self.midichans[c.chipindex]) for c in self.channels)
    if text != self.prevtext:
      log.debug(text)
      self.prevtext = text
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
