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

from pym2149.ym2149 import stclock
from pym2149.program import DefaultNote
from pym2149.const import midichannelcount

outputrate = 44100
'''May be ignored e.g. when sending data to JACK we must use its own rate.'''

freqclamp = True
'''Whether inaudible tones are clamped to the lowest such tone. Setting this to True improves performance when very high frequency tones are used to attenuate the envelope. Quality may be degraded, particularly at lower outputrates.'''

underclock = 8
'''The number of nominal clock ticks until the chip state can next be updated, must be a factor of 8 i.e. in {1, 2, 4, 8}. Higher numbers improve performance but the authentic setting is currently unknown.'''

oscpause = False
'''Whether an oscillator is paused when turned off in the mixer. This option doesn't significantly help performance so it's a bit useless.'''

contextclock = stclock
'''Modified if a file is being played that specifies its own clock.'''

nominalclock = config.contextclock
'''You can specify your own clock here, which overrides any other value.'''

stereo = False

panlaw = 3

maxpan = .75

defaultignoreloop = False
'''Modified to True when writing to a file.'''

ignoreloop = config.defaultignoreloop
'''If True playback will not loop.'''

pianorollheight = config.contextpianorollheight
'''You can override the deduced piano roll height here.'''

midichannelbase = 1

midiprogrambase = 0

neutralvelocity = 0x60

velocityperlevel = 0x10

midiprograms = dict([config.midiprogrambase + i, DefaultNote] for i in xrange(midichannelcount))

midichanneltoprogram = dict([config.midichannelbase + i, config.midiprogrambase + i] for i in xrange(midichannelcount))

pitchbendpersemitone = 0x200
'''The default of 0x200 is 4 coarse steps per semitone, or 25 cents per coarse step, or a radius of 16 semitones.'''

finepitchbendisrate = False
'''If True, the fine part of pitch bend is interpreted as a rate per chip update.'''

dosoundextraseconds = 3
