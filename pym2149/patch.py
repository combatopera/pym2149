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
    self.chip = chip
    self.index = index

  def noteon(self, pitch): pass

  def noteonframe(self, frame): pass

  def noteoff(self): pass

  def noteoffframe(self, frame): pass

class DefaultPatch(Patch):

  def noteon(self, pitch):
    self.chip.toneperiods[self.index].value = pitch.freq().toneperiod(self.chip.nominalclock())
    self.chip.toneflags[self.index].value = True
    self.chip.fixedlevels[self.index].value = 15

  def noteoffframe(self, frame):
    self.chip.fixedlevels[self.index].value = max(14 - frame // 2, 0)
