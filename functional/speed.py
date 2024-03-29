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

from lurlene import V, E

class Speed:

    def on(self, ym):
        ym.toneflag = True
        ym.level = 10
        ym.tonefreq = 440

    def off(self, speeds, frame):
        global speed
        if V(f"{speed - 1}x 1")[frame]:
            speed = speeds[frame]

sections = [[E(Speed, 'r.5', speeds = V('20 10 30'))]]
speed = 30
