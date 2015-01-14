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
from pym2149.program import FX
from pym2149.midi import Midi
from pym2149 import midichannelcount
from pym2149.mediation import Mediation
from pym2149.config import getprocessconfig

log = logging.getLogger(__name__)

class Channel:

  def __init__(self, config, chipindex, chip):
    neutralvel = config.neutralvelocity
    velperlevel = config.velocityperlevel
    self.tovoladj = lambda vel: (vel - neutralvel + velperlevel // 2) // velperlevel
    self.onornone = None
    self.chipindex = chipindex
    self.chip = chip
    self.note = None

  def programornone(self):
    return None if self.note is None else self.note.__class__

  def newnote(self, frame, program, midinote, vel, fx):
    self.onornone = True
    self.onframe = frame
    self.note = program(self.chip, self.chipindex, Pitch(midinote), fx)
    self.voladj = self.tovoladj(vel)

  def noteoff(self, frame):
    self.onornone = False
    self.offframe = frame

  def update(self, frame):
    if self.onornone:
      f = frame - self.onframe
      if not f:
        self.noteonimpl()
      self.note.noteonframe(f)
    elif self.onornone is not None: # It's False.
      if self.onframe == self.offframe:
        self.noteonimpl()
      f = frame - self.offframe
      if not f:
        self.note.noteoff()
      self.note.noteoffframe(self.offframe - self.onframe, f)

  def noteonimpl(self):
    # Make it so that the note only has to switch things on:
    self.chip.flagsoff(self.chipindex)
    self.note.noteon(self.voladj)

  def __str__(self):
    return chr(ord('A') + self.chipindex)

class Channels:

  def __init__(self, config, chip):
    self.channels = [Channel(config, i, chip) for i in xrange(chip.channels)]
    self.midiprograms = config.midiprograms
    self.midichantoprogram = dict([c, self.midiprograms[p]] for c, p in config.midichanneltoprogram.iteritems())
    self.midichantofx = dict([config.midichannelbase + i, FX()] for i in xrange(midichannelcount))
    self.mediation = Mediation(config.midichannelbase, chip.channels)
    self.prevtext = None

  def noteon(self, frame, midichan, midinote, vel):
    program = self.midichantoprogram[midichan]
    fx = self.midichantofx[midichan]
    channel = self.channels[self.mediation.acquirechipchan(midichan, midinote, frame)]
    channel.newnote(frame, program, midinote, vel, fx)
    return channel

  def noteoff(self, frame, midichan, midinote, vel):
    chipchan = self.mediation.releasechipchan(midichan, midinote)
    if chipchan is not None:
      channel = self.channels[chipchan]
      channel.noteoff(frame)
      return channel

  def pitchbend(self, frame, midichan, bend):
    self.midichantofx[midichan].bend = bend

  def programchange(self, frame, midichan, program):
    self.midichantoprogram[midichan] = self.midiprograms[program]

  def updateall(self, frame):
    text = ' | '.join("%s@%s" % (c.programornone(), self.mediation.currentmidichanandnote(c.chipindex)[0]) for c in self.channels)
    if text != self.prevtext:
      log.debug(text)
      self.prevtext = text
    for channel in self.channels:
      channel.update(frame)

  def __str__(self):
    return ', '.join("%s -> %s" % entry for entry in sorted(self.midichantoprogram.iteritems()))

def main():
  config = getprocessconfig()
  midi = Midi(config)
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
