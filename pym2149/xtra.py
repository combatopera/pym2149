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

from .lc import V, D, _topitch, major
from .pitches import E4

class XTRA:

    degree = D('-') + D('- 5- 1 5,+').of(6)
    envflag = V('30x,1')
    mute = False

    def on(self, chip, frame):
        if self.mute:
            return
        envflag = self.envflag[frame]
        pitch = _topitch(major, 1, E4, self.degree[frame])
        for chan in range(min(3, len(chip._chanproxies))):
            chip[chan].toneflag = True
            chip[chan].level = 15
            chip[chan].envflag = envflag
            chip[chan].tonepitch = pitch
            chip[chan].toneperiod += chan * 2
        if envflag and not self.envflag[frame - 1]:
            chip.envshape = 0
        chip.envperiod = 30 << 8

    def off(self):
        type(self).mute = True
