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

A_fine.put(0x00)
rough1 = 0x06
rough2 = 0x08
A_rough.put(rough2)
mixer.put(A_tone)
for i in range(5):
  A_level.put(0x0f)
  sleep(2 + i)
  A_level.put(0x0d)
  sleep(2 + i)
for i in range(10):
  A_rough.put(rough1)
  A_level.put(0x0d)
  sleep(2 + i)
  A_rough.put(rough2)
  A_level.put(0x0f)
  sleep(2 + i)
A_level.put(0x00)
