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

mixer.put() # All off.
def reset():
  for l in A_level, B_level, C_level:
    l.put(0x0d) # Half amplitude.
reset()
sleep(50) # Allow it to settle at DC 0.
for a in range(0x10):
  for b in range(0x10):
    for c in range(0x10):
      A_level.put(a)
      B_level.put(b)
      C_level.put(c)
      sleep(2)
      reset()
      sleep(2)
