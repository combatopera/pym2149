# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

mixer.put(A_tone)
A_level.put(0x0f)
B_level.put(0x00)
def spike(): # Doesn't work, never mind.
  B_level.put(0x0d)
  B_level.put(0x00)
A_fine.put(0x00)
for i in range(20):
  spike()
  A_rough.put(0x0e)
  sleep(2 + i)
  spike()
  A_rough.put(0x02)
  sleep(2 + i)
A_level.put(0x00)
B_level.put(0x00)
