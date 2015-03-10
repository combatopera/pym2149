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

class FX:

  bendlowerbound = -0x2000
  bendupperbound = -bendlowerbound - 1

  @staticmethod
  def signum(n):
    return 1 if n > 0 else (-1 if n < 0 else 0)

  def __init__(self, config):
    self.bendpersemitone = config.pitchbendpersemitone
    self.bend = 0
    self.bendrate = 0
    self.bendlimit = self.bendlowerbound # Or 0 absolute.

  def applyrates(self):
    side = self.signum(self.bend - self.bendlimit)
    self.bend = max(self.bendlowerbound, min(self.bendupperbound, self.bend + self.bendrate))
    if side != self.signum(self.bend - self.bendlimit):
      self.bend = self.bendlimit

  def bendsemitones(self):
    return self.bend / self.bendpersemitone

class Note:

  def __init__(self, nomclock, chip, chipchan, pitch, fx):
    self.toneperiod = chip.toneperiods[chipchan]
    self.toneflag = chip.toneflags[chipchan]
    self.noiseflag = chip.noiseflags[chipchan]
    self.fixedlevel = chip.fixedlevels[chipchan]
    self.levelmode = chip.levelmodes[chipchan]
    self.nomclock = nomclock
    self.chip = chip
    self.chipchan = chipchan
    self.pitch = pitch
    self.fx = fx

  def applypitch(self, pitch = None):
    self.applyfreq(((self.pitch if pitch is None else pitch) + self.fx.bendsemitones()).freq())

  def applyfreq(self, freq):
    self.toneperiod.value = freq.toneperiod(self.nomclock)

  def setfixedlevel(self, unclamped):
    self.fixedlevel.value = max(0, min(15, unclamped))

  def callnoteon(self, voladj):
    self.voladj = voladj
    self.noteon()

  def noteon(self): pass

  def noteonframe(self, frame):
    """Note this may never be called, so should not make changes that noteoff or a custom impl of noteoffframe later relies on."""

  def callnoteoff(self, onframes):
    self.onframes = onframes
    self.noteoff()

  def noteoff(self): pass

  def noteoffframe(self, frame):
    self.noteonframe(self.onframes + frame) # FIXME: Has failed due to lack of onframes.

class NullNote(Note): pass

class DefaultNote(Note):

  def noteon(self):
    self.toneflag.value = True
    self.setfixedlevel(self.voladj + 13)

  def noteonframe(self, frame):
    self.applypitch()

  def noteoffframe(self, frame):
    self.setfixedlevel(self.voladj + 12 - frame // 2)

class Unpitched(Note):

  def __init__(self, *args):
    Note.__init__(self, *args)
    self.note = self.midinotetoprogram.get(self.pitch, NullNote)(self.nomclock, self.chip, self.chipchan, None, self.fx)

  def noteon(self):
    self.note.callnoteon(self.voladj)

  def noteonframe(self, frame):
    self.note.noteonframe(frame)

  def noteoff(self):
    self.note.callnoteoff(self.onframes)

  def noteoffframe(self, frame):
    self.note.noteoffframe(frame)
