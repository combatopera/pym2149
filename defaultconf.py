# Copyright 2014 Andrzej Cichocki

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

outputrate = 44100
'''May be ignored e.g. when sending data to JACK we must use its own rate.'''

freqclamp = False
'''Whether inaudible tones are clamped to the lowest such tone. Setting this to True improves performance when very high frequency tones are used to attenuate the envelope.'''

statestride = 1
'''The number of nominal clock ticks until the chip state can next be updated, must be a factor of 8 i.e. in {1, 2, 4, 8}. Higher numbers improve performance but the authentic setting is currently unknown.'''

oscpause = False
'''Whether an oscillator is paused when turned off in the mixer. This option doesn't significantly help performance so it's a bit useless.'''

nominalclockornone = None
'''Overrides any context clock rate. If None and there is no context clock, the default is the ST rate of 2 MHz.'''

stereo = False

panlaw = 3

ignoreloop = False
'''If True playback will not loop.'''

pianorollheightornone = None
'''If not None, override the deduced piano roll height.'''
