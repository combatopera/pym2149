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

class FX:

  maxbend = 1 << 13

  def __init__(self):
    self.bend = 0

class Patch:

  def __init__(self, chip, index):
    self.toneperiod = chip.toneperiods[index]
    self.toneflag = chip.toneflags[index]
    self.noiseflag = chip.noiseflags[index]
    self.fixedlevel = chip.fixedlevels[index]
    self.chip = chip
    self.index = index

  def applypitch(self, pitch):
    self.applyfreq(pitch.freq())

  def applyfreq(self, freq):
    self.toneperiod.value = freq.toneperiod(self.chip.nominalclock())

  def setfixedlevel(self, unclamped):
    self.fixedlevel.value = max(0, min(15, unclamped))

  # This is the point at which a logical channel (self) is mapped to a physical one (index).
  def noteon(self, pitch, voladj, fx): pass

  def noteonframe(self, frame): pass

  def noteoff(self): pass

  def noteoffframe(self, onframes, frame):
    self.noteonframe(onframes + frame)

  def __str__(self):
    return str(self.__class__) # XXX: Disambiguate instances?

class NullPatch(Patch): pass

class DefaultPatch(Patch):

  def noteon(self, pitch, voladj, fx):
    self.applypitch(pitch)
    self.toneflag.value = True
    self.setfixedlevel(voladj + 13)
    self.voladj = voladj

  def noteoffframe(self, onframes, frame):
    self.setfixedlevel(self.voladj + 12 - frame // 2)

class Kit(Patch):

  def __init__(self, *args, **kwargs):
    Patch.__init__(self, *args, **kwargs)
    self.midinotetopatch = {}

  def __setitem__(self, midinote, patch):
    self.midinotetopatch[midinote] = patch

  def noteon(self, pitch, voladj, fx):
    self.patch = self.midinotetopatch.get(pitch, NullPatch)(self.chip, self.index)
    self.patch.noteon(None, voladj, fx)

  def noteonframe(self, frame):
    self.patch.noteonframe(frame)

  def noteoff(self):
    self.patch.noteoff()

  def noteoffframe(self, onframes, frame):
    self.patch.noteoffframe(onframes, frame)
