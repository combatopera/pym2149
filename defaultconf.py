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

freqclamp = True # XXX: Does this sound worse, particularly at lower outputrates?
'''Whether inaudible tones are clamped to the lowest such tone. Setting this to True improves performance when very high frequency tones are used to attenuate the envelope.'''

underclock = 8
'''The number of nominal clock ticks until the chip state can next be updated, must be a factor of 8 i.e. in {1, 2, 4, 8}. Higher numbers improve performance but the authentic setting is currently unknown.'''

oscpause = False
'''Whether an oscillator is paused when turned off in the mixer. This option doesn't significantly help performance so it's a bit useless.'''

from pym2149.ym2149 import stclock as defaultclock
'''Used when there is no context clock or override.'''

clockoverrideornone = None
'''If not None, override the context clock.'''

stereo = False

panlaw = 3

maxpan = .75

ignoreloop = False
'''If True playback will not loop. This default is modified to True when writing to a file.'''

pianorollheightornone = None
'''If not None, override the deduced piano roll height.'''

from pym2149.patch import Patches, DefaultPatch
patches = Patches()
'''For each MIDI channel, the patch class and chip channel restriction string. For example, the string may be 'AB' for 2-note polyphony.'''
for i in xrange(3): patches[1 + i] = DefaultPatch, chr(ord('A') + i)
