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
from pym2149.iface import YMFile, JackConnection
import operator

outputrate = config.di(JackConnection).outputrate if config.di.all(JackConnection) else 44100
'''Note this does not have the power to modify the JACK output rate, only pym2149's impression of it.'''

freqclamp = True
'''Whether inaudible tones are clamped to the lowest such tone. Setting this to True improves performance when very high frequency tones are used to attenuate the envelope. Quality may be degraded, particularly at lower outputrates.'''

underclock = 8
'''The number of nominal clock ticks until the chip state can next be updated, must be a factor of 8 i.e. in {1, 2, 4, 8}. Higher numbers improve performance. I don't know which setting is authentic.'''

oscpause = False
'''Whether an oscillator is paused when turned off in the mixer. This option doesn't significantly help performance so it's a bit useless.'''

nominalclock = config.di(YMFile).nominalclock if config.di.all(YMFile) else stclock
'''You can specify your own clock here, which overrides any other value.'''

midipan = False
'''Pay attention to MIDI panning rather than having an automatic fixed pan per channel.'''

stereo = config.midipan

panlaw = 3
# TODO: Document how this works.

maxpan = .75
'''The pan of the outermost channels when panning automatically.'''

systemchannelcount = 2

ignoreloop = hasattr(config, 'outpath')
'''If True playback will not loop.'''

updaterate = config.di(YMFile).updaterate if config.di.all(YMFile) else 50

linesperbeat = 4
'''bpmtool.py uses this.'''

pianorollheight = config.di(YMFile).pianorollheight
'''You can override the deduced piano roll height here.'''

midichannelbase = 1
'''In case you wanted 0-based channel numbering.'''

midiprogrambase = 0
'''Some synths use 1 for the first program.'''

neutralvelocity = 0x60

velocityperlevel = 0x10

midiprograms = dict([config.midiprogrambase + i, DefaultNote] for i in xrange(0x80))
'''Program number to Note subclass.'''

midichanneltoprogram = dict([config.midichannelbase + i, config.midiprogrambase + i] for i in xrange(midichannelcount))
'''Initial assignment of programs to channels.'''

pitchbendpersemitone = 0x200
'''The default of 0x200 is 4 coarse steps per semitone, or 25 cents per coarse step, or a radius of 16 semitones.'''

pitchbendratecontroller = None
'''If not None, the 0-based MIDI controller number for change of pitch bend per update.'''

pitchbendlimitcontroller = None
'''If not None, the 0-based MIDI controller number for the pitch bend value to stop at.'''

pitchbendratecontrollershift = 0
'''The number of least-significant bits to strip from the pitchbendratecontroller value. You can set this to 7 to forget about the fine byte and just use the coarse one.'''
# TODO: Replace this and pitchbendpersemitone with a more general config for controller resolution.

dosoundextraseconds = 3
'''When playing a Dosound script, the amount of time to continue rendering after end of script.'''

chipchannels = 3
'''The number of chip channels to implement.''' # TODO: Make values other than 3 work.

profile = None
'''If not None, a tuple of (profiling time, sort column, output path).''' # TODO: Let's not use tuples.

trace = None
'''If not None, the number of seconds worth of trace data to collect.'''

plltargetpos = operator.truediv(.5, config.updaterate) # TODO: Make it possible to use slash here.
'''The target median shift in seconds between the start of a MIDI event processing window (of size 1/updaterate) and the events in that window. Higher values (i.e. MIDI events closer to end of window and thus our processing of them) improve latency at increased risk of unstable timing (we don't want any events to stray into the next window).'''

pllalpha = .1
'''The alpha value for the exponential moving average we use for convergence to plltargetpos.'''

jackringsize = 2 if config.di.all(YMFile) else 10
'''In the YMFile case, two buffers allows us to prepare another while waiting for JACK to process the one.'''

jackcoupling = bool(config.di.all(YMFile))
'''If True, JACK overrun (i.e. waiting for it to release a buffer) is considered a normal condition.'''

zerovelocityisnoteoffchannels = ()
'''My AZ-1 appears to send Note On with zero velocity instead of Note Off, so its channel goes here.'''

performancechannels = ()
'''Events from these MIDI channels are treated as unscheduled, so contribute to neither the PLL nor speed detector.'''

monophonicchannels = ()
'''In each of these MIDI channels the maximum number of 'on' notes is restricted to one. This is useful if you want your MIDI controller to affect just one chip channel, for example.'''

midiskipenabled = True
'''For real-time performance this should be True to minimise latency. For rendering this should be False to avoid unstable timing.'''

speeddetector = True
'''Set to False to turn off the speed detector and save some CPU.'''
