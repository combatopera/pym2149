# Copyright 2014, 2018, 2019 Andrzej Cichocki

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

from . import E, V

class Bias:

    fire = V('5x 1')

    def on(self, ym, frame):
        ym.level = 1
        ym.toneflag = True
        ym.toneperiod = 1000 + 10 * frame
        if self.fire[frame]:
            global sections
            sections = [(E(Bias2, '2'),)]

class Bias2:

    fire = V('5x 1,0')

    def on(self, ym, frame):
        ym.level = 2
        ym.toneflag = True
        ym.toneperiod = 1000 + 10 * frame
        if self.fire[frame]:
            global speed
            speed = 7 # The next frame will be 7.5 as we assume 6.5 has happened.

sections = [(E(Bias, '100'),)]
speed = 6
