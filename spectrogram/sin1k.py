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
from pym2149.dac import SinusEffect
from pym2149.lc import E

# TODO LATER: Find out why the result appears shifted a few samples to the right.
class Sin1k:

    def on(self, chip, frame):
        chip.fixedlevel = max(0, 15 - frame // 5) # FIXME: Implement clamping already.
        if frame < 1:
            chan = chip[0]._chan
            timer = chip._chip.timers[chan]
            timer.effect.value = SinusEffect(chip._chip.fixedlevels[chan])
            timer.freq.value = 1000 * 4 # FIXME: It should know wavelength from effect.

silence = E(Silence, '4')
A = E(Sin1k, '4'), silence, silence
sections = A,
speed = 25
