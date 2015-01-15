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

  bendlimit = 0x2000

  def __init__(self, config):
    self.bendradius = config.pitchbendradius
    self.resetbend()

  def resetbend(self):
    self.bend = 0
    self.bendrate = 0

  def applyrates(self):
    self.bend = max(-self.bendlimit, min(self.bendlimit - 1, self.bend + self.bendrate))

  def bendsemitones(self):
    return self.bend / self.bendlimit * self.bendradius

class Note:

  def __init__(self, chip, chipchan, pitch, fx):
    self.toneperiod = chip.toneperiods[chipchan]
    self.toneflag = chip.toneflags[chipchan]
    self.noiseflag = chip.noiseflags[chipchan]
    self.fixedlevel = chip.fixedlevels[chipchan]
    self.levelmode = chip.levelmodes[chipchan]
    self.chip = chip
    self.chipchan = chipchan
    self.pitch = pitch
    self.fx = fx

  def applypitch(self, pitch = None):
    self.applyfreq(((self.pitch if pitch is None else pitch) + self.fx.bendsemitones()).freq())

  def applyfreq(self, freq):
    self.toneperiod.value = freq.toneperiod(self.chip.nominalclock())

  def setfixedlevel(self, unclamped):
    self.fixedlevel.value = max(0, min(15, unclamped))

  def noteon(self, voladj): pass

  def noteonframe(self, frame): pass

  def noteoff(self): pass

  def noteoffframe(self, onframes, frame):
    self.noteonframe(onframes + frame)

class NullNote(Note): pass

class DefaultNote(Note):

  def noteon(self, voladj):
    self.toneflag.value = True
    self.setfixedlevel(voladj + 13)
    self.voladj = voladj

  def noteonframe(self, frame):
    self.applypitch()

  def noteoffframe(self, onframes, frame):
    self.setfixedlevel(self.voladj + 12 - frame // 2)

class Unpitched(Note):

  def noteon(self, voladj):
    self.note = self.midinotetoprogram.get(self.pitch, NullNote)(self.chip, self.chipchan, None, self.fx)
    self.note.noteon(voladj)

  def noteonframe(self, frame):
    self.note.noteonframe(frame)

  def noteoff(self):
    self.note.noteoff()

  def noteoffframe(self, onframes, frame):
    self.note.noteoffframe(onframes, frame)
