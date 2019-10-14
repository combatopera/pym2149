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

from spectrogram import Silence
from pym2149.lc import E, V
from pym2149.pitch import Freq

class T:

    def on(self, chip, freq, frame):
        chip.toneflag = True
        chip.fixedlevel = 15
        chip.toneperiod = Freq(freq[frame]).toneperiod(chip._nomclock)

silence = E(Silence, '1')
A = E(T, '1', freq = V('1000 2000 3000 4000')), silence, silence
sections = A,
speed = 50/4
