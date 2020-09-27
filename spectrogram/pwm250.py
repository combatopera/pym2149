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

from . import E
from pym2149.dac import PWMEffect
from spectrogram import silence

class PWM250:

    def on(self, ym, frame):
        ym.toneflag = True
        ym.level = 15
        ym.tonefreq = 250
        if frame < 1:
            chan = ym[0]._chan
            timer = ym._chip.timers[chan]
            timer.effect.value = PWMEffect(ym._chip.fixedlevels[chan])
            timer.freq.value = 250

sections = [[E(PWM250, '1.5'), silence, silence]]
speed = 50
