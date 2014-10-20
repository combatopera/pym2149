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

  def noteon(self, pitch, voladj): pass

  def noteonframe(self, frame, bend): pass

  def noteoff(self): pass

  def noteoffframe(self, onframes, frame, bend):
    self.noteonframe(onframes + frame, bend)

class NullPatch(Patch): pass

class DefaultPatch(Patch):

  def noteon(self, pitch, voladj):
    self.applypitch(pitch)
    self.toneflag.value = True
    self.setfixedlevel(voladj + 13)
    self.voladj = voladj

  def noteoffframe(self, onframes, frame, bend):
    self.setfixedlevel(self.voladj + 12 - frame // 2)

class PatchInfo:

  def __init__(self, patch, restrict):
    self.patch = patch
    self.restrict = restrict

  def __str__(self):
    return "(%s %s)" % (self.restrict, self.patch.__name__)

class Patches:

  def __init__(self):
    self.infos = {}

  def __setitem__(self, midichan, t):
    self.infos[midichan] = PatchInfo(*t)

  def __getitem__(self, midichan):
    return self.infos[midichan]

  def iteritems(self):
    return self.infos.iteritems()

class Kit(Patch):

  def __init__(self, *args, **kwargs):
    Patch.__init__(self, *args, **kwargs)
    self.midinotetopatch = {}

  def __setitem__(self, midinote, patch):
    self.midinotetopatch[midinote] = patch

  def noteon(self, pitch, voladj):
    self.patch = self.midinotetopatch.get(pitch, NullPatch)(self.chip, self.index)
    self.patch.noteon(None, voladj)

  def noteonframe(self, frame, bend):
    self.patch.noteonframe(frame, bend)

  def noteoff(self):
    self.patch.noteoff()

  def noteoffframe(self, onframes, frame, bend):
    self.patch.noteoffframe(onframes, frame, bend)
