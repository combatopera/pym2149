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

class Lfsr:

    def __init__(self, nzdegrees):
        self.mask = sum(1 << (nzd - 1) for nzd in nzdegrees)
        self.x = 1

    def __call__(self):
        bit = self.x & 1
        self.x >>= 1
        if bit:
            self.x ^= self.mask
        return 1 - bit # Authentic, see qnoispec.

    def __iter__(self):
        first = self.x
        while True:
            yield self()
            if first == self.x:
                break
