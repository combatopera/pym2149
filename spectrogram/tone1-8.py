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

from . import E, V
from spectrogram import silence

class T:

    def on(self, ym, period, frame):
        ym.toneflag = True
        ym.level = 15
        ym.toneperiod = period[frame]

sections = [[E(T, '.125', period = V('1 2 3 4 5 6 7 8').of(.125)), silence, silence]]
speed = 50
