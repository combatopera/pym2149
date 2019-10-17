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

from spectrogram import silence
from pym2149.dac import PWMEffect
from pym2149.lc import E

class PWM100:

    def on(self, chip, frame):
        chip.toneflag = True
        chip.level = 15
        chip.tonefreq = 100
        if frame < 1:
            chan = chip[0]._chan
            timer = chip._chip.timers[chan]
            timer.effect.value = PWMEffect(chip._chip.fixedlevels[chan])
            timer.freq.value = 101 # Necessarily detune.

sections = [[E(PWM100, '1.5'), silence, silence]]
speed = 50
