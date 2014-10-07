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
    self.fixedlevel = chip.fixedlevels[index]
    self.chip = chip
    self.index = index

  def applypitch(self, pitch):
    self.toneperiod.value = pitch.freq().toneperiod(self.chip.nominalclock())

  def setfixedlevel(self, unclamped):
    self.fixedlevel.value = max(0, min(15, unclamped))

  def noteon(self, pitch, voladj): pass

  def noteonframe(self, frame): pass

  def noteoff(self): pass

  def noteoffframe(self, frame): pass

class DefaultPatch(Patch):

  def noteon(self, pitch, voladj):
    self.applypitch(pitch)
    self.toneflag.value = True
    self.setfixedlevel(voladj + 13)
    self.voladj = voladj

  def noteoffframe(self, frame):
    self.setfixedlevel(self.voladj + 12 - frame // 2)
