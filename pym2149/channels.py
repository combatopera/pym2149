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
import logging
from pym2149.pitch import Pitch
from pym2149.program import FX
from pym2149.const import midichannelcount
from pym2149.mediation import Mediation
from pym2149.di import types
from pym2149.iface import Chip, Config

log = logging.getLogger(__name__)

class Channel:

  def __init__(self, config, chipindex, chip):
    self.nomclock = config.nominalclock
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
    self.note = program(self.nomclock, self.chip, self.chipindex, Pitch(midinote), fx)
    self.voladj = self.tovoladj(vel)

  def noteoff(self, frame):
    self.onornone = False
    self.offframe = frame

  def update(self, frame):
    if self.onornone:
      f = frame - self.onframe
      if not f:
        self.noteonimpl()
      self.note.noteonframe(f) # May never be called, so noteoff/noteoffframe should not rely on side-effects.
    elif self.onornone is not None: # It's False.
      if self.onframe == self.offframe:
        self.noteonimpl()
      f = frame - self.offframe
      if not f:
        self.note.callnoteoff(self.offframe - self.onframe)
      self.note.noteoffframe(f)

  def noteonimpl(self):
    # Make it so that the note only has to switch things on:
    self.chip.flagsoff(self.chipindex)
    self.note.callnoteon(self.voladj)

  def getpan(self):
    return 0 if self.note is None else self.note.fx.normpan()

  def __str__(self):
    return chr(ord('A') + self.chipindex)

class ControlPair:

  def __init__(self, binaryzero, flush):
    self.binary = self.binaryzero = binaryzero
    self.flush = flush

  def install(self, d, msbindex):
    d[msbindex] = self.setmsb
    d[msbindex + 0x20] = self.setlsb

  def setmsb(self, midichan, msb):
    self.binary = (msb << 7) | (self.binary & 0x7f)
    self.flush(midichan, self.binary - self.binaryzero)

  def setlsb(self, midichan, lsb):
    self.binary = (self.binary & (0x7f << 7)) | lsb
    self.flush(midichan, self.binary - self.binaryzero)

class Channels:

  @types(Config, Chip)
  def __init__(self, config, chip):
    self.channels = [Channel(config, i, chip) for i in xrange(config.chipchannels)]
    self.midiprograms = config.midiprograms
    self.midichantoprogram = dict([c, self.midiprograms[p]] for c, p in config.midichanneltoprogram.iteritems())
    self.midichantofx = dict([config.midichannelbase + i, FX(config)] for i in xrange(midichannelcount))
    self.mediation = Mediation(config.midichannelbase, config.chipchannels)
    self.controllers = {}
    def flush(midichan, value):
      self.midichantofx[midichan].modulation = value
    ControlPair(0, flush).install(self.controllers, 0x01)
    def flush(midichan, value):
      self.midichantofx[midichan].pan = value
    ControlPair(0x2000, flush).install(self.controllers, 0x0a)
    if config.pitchbendratecontroller is not None:
      def flush(midichan, value):
        self.midichantofx[midichan].bendrate = value
      ControlPair(0x2000, flush).install(self.controllers, config.pitchbendratecontroller)
    if config.pitchbendlimitcontroller is not None:
      def flush(midichan, value):
        self.midichantofx[midichan].bendlimit = value
      ControlPair(0x2000, flush).install(self.controllers, config.pitchbendlimitcontroller)
    self.prevtext = None
    self.frameindex = 0

  def noteon(self, midichan, midinote, vel):
    program = self.midichantoprogram[midichan]
    fx = self.midichantofx[midichan]
    channel = self.channels[self.mediation.acquirechipchan(midichan, midinote, self.frameindex)]
    channel.newnote(self.frameindex, program, midinote, vel, fx)
    return channel

  def noteoff(self, midichan, midinote, vel):
    chipchan = self.mediation.releasechipchan(midichan, midinote)
    if chipchan is not None:
      channel = self.channels[chipchan]
      channel.noteoff(self.frameindex)
      return channel

  def pitchbend(self, midichan, bend):
    self.midichantofx[midichan].bend = bend

  def controlchange(self, midichan, controller, value):
    if controller in self.controllers:
      self.controllers[controller](midichan, value)

  def programchange(self, midichan, program):
    self.midichantoprogram[midichan] = self.midiprograms[program]

  def updateall(self):
    text = ' | '.join("%s@%s" % (c.programornone(), self.mediation.currentmidichanandnote(c.chipindex)[0]) for c in self.channels)
    if text != self.prevtext:
      log.debug(text)
      self.prevtext = text
    for channel in self.channels:
      channel.update(self.frameindex)

  def closeframe(self):
    for fx in self.midichantofx.itervalues():
      fx.applyrates()
    self.frameindex += 1

  def getpans(self):
    for c in self.channels:
      yield c.getpan()

  def __str__(self):
    return ', '.join("%s -> %s" % entry for entry in sorted(self.midichantoprogram.iteritems()))
