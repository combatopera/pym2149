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

from . import topitch
from .util import threadlocals
from ..clock import ClockInfo
from ..iface import Config, Prerecorded, Tuning, Context
from ..reg import regproperty, Reg
from ..util import ExceptionCatcher, singleton
from diapyr import types
from diapyr.util import innerclass
from functools import partial
import logging, bisect, difflib, numpy as np

log = logging.getLogger(__name__)

def _convenience(name):
    def fget(self):
        return getattr(self._chanproxies[0], name)
    def fset(self, value):
        setattr(self._chanproxies[0], name, value)
    return property(fget, fset)

class ChanProxy:

    tonefreq = regproperty(lambda self: self.tonefreqreg)
    level = regproperty(lambda self: self.levelreg)
    noiseflag = regproperty(lambda self: self._chip.noiseflags[self._chan])
    toneflag = regproperty(lambda self: self._chip.toneflags[self._chan])
    toneperiod = regproperty(lambda self: self.toneperiodreg)
    tonepitch = regproperty(lambda self: self.tonepitchreg)
    tonedegree = regproperty(lambda self: self.tonedegreereg)
    envflag = regproperty(lambda self: self._chip.levelmodes[self._chan])

    def __init__(self, chip, chan, clock, tuning):
        self.tonedegreereg = Reg()
        self.tonepitchreg = Reg().link(topitch, self.tonedegreereg)
        self.tonefreqreg = Reg().link(tuning.freq, self.tonepitchreg)
        self.toneperiodreg = Reg().link(clock.toneperiod, self.tonefreqreg)
        chip.toneperiods[chan].link(round, self.toneperiodreg)
        self.levelreg = Reg()
        chip.fixedlevels[chan].link(round, self.levelreg)
        self._chip = chip
        self._chan = chan

class ChipRegs:

    def __init__(self, chip, clock, tuning):
        self.noisefreqreg = Reg()
        self.noiseperiodreg = Reg().link(clock.noiseperiod, self.noisefreqreg)
        chip.noiseperiod.link(round, self.noiseperiodreg)
        self.envdegreereg = Reg()
        self.envpitchreg = Reg().link(topitch, self.envdegreereg)
        self.envfreqreg = Reg().link(tuning.freq, self.envpitchreg)
        self.envperiodreg = Reg().link(lambda f, s: clock.envperiod(f, s), self.envfreqreg, chip.envshape)
        chip.envperiod.link(round, self.envperiodreg)

class ChipProxy(ExceptionCatcher):

    noiseperiod = regproperty(lambda self: self._chipregs.noiseperiodreg)
    envshape = regproperty(lambda self: self._chip.envshape)
    envperiod = regproperty(lambda self: self._chipregs.envperiodreg)
    envpitch = regproperty(lambda self: self._chipregs.envpitchreg)
    envdegree = regproperty(lambda self: self._chipregs.envdegreereg)
    noisefreq = regproperty(lambda self: self._chipregs.noisefreqreg)
    envfreq = regproperty(lambda self: self._chipregs.envfreqreg)

    def __init__(self, chip, chan, chanproxies, chipregs):
        self._letter = chr(ord('A') + chan)
        self._chanproxies = chanproxies[chan:] + chanproxies[:chan]
        self._chip = chip
        self._chipregs = chipregs

    def __getitem__(self, index):
        return self._chanproxies[index]

    def noisepriority(self):
        return not any(chan.noiseflag for chan in self._chanproxies[1:])

for name in dir(ChanProxy):
    if '_' != name[0]:
        setattr(ChipProxy, name, _convenience(name))
del name

class NoSuchSectionException(Exception): pass

class LiveCodingBridge(Prerecorded):

    bias = .5 # TODO: Make configurable for predictable swing in odd speed case.

    @types(Config, ClockInfo, Tuning, Context)
    def __init__(self, config, clock, tuning, context):
        self.loop = not config.ignoreloop
        self.sectionname = config.section
        self.chancount = config.chipchannels
        self.clock = clock
        self.tuning = tuning
        self.context = context

    @property
    def pianorollheight(self):
        return self.context.speed

    @innerclass
    class Session(ExceptionCatcher):

        def __init__(self, chip):
            chipregs = ChipRegs(chip, self.clock, self.tuning)
            chanproxies = [ChanProxy(chip, chan, self.clock, self.tuning) for chan in range(self.chancount)]
            self.chipproxies = [ChipProxy(chip, chan, chanproxies, chipregs) for chan in range(self.chancount)]

        def _quiet(self):
            for proxy in self.chipproxies:
                proxy.noiseflag = False
                proxy.toneflag = False
                proxy.envflag = False
                proxy.level = 0

        def _step(self, speed, section, frame):
            self._quiet()
            for proxy, pattern in zip(self.chipproxies, section):
                with proxy.catch("Channel %s update failed:", proxy._letter):
                    pattern.apply(speed, frame, proxy)

    def _startframe(self, sectionindex):
        return self.context.cumulativeframecounts[sectionindex - 1] if sectionindex else 0

    def _initialframe(self):
        if self.sectionname is None:
            return 0
        section = getattr(self.context, self.sectionname)
        try:
            i = self.context.sections.index(section)
        except ValueError:
            raise NoSuchSectionException(self.sectionname)
        return self._startframe(i)

    def _sectionandframe(self, frame):
        sectionends = self.context.cumulativeframecounts
        frame %= sectionends[-1]
        i = bisect.bisect(sectionends, frame)
        return self.context.sections[i], frame - self._startframe(i)

    def frames(self, chip):
        session = self.Session(chip)
        frameindex = self._initialframe() + self.bias
        with threadlocals(context = self.context):
            while self.loop or frameindex < self.context.totalframecount:
                oldspeed = self.context.speed
                oldsections = self.context.sections
                frame = session._quiet
                if self.context.totalframecount: # Otherwise freeze until there is something to play.
                    with session.catch('Failed to prepare a frame:'):
                        frame = partial(session._step, self.context.speed, *self._sectionandframe(frameindex))
                        frameindex += 1
                frame()
                yield
                self.context._flip()
                if oldspeed != self.context.speed:
                    frameindex = (frameindex - self.bias) / oldspeed * self.context.speed + self.bias
                if oldsections != self.context.sections:
                    frameindex = self.adjustframeindex(oldsections, frameindex)

    def adjustframeindex(self, oldsections, frameindex):
        oldsectionends = np.cumsum([self.context.speed * max(p.len for p in s) for s in oldsections])
        sectionends = np.cumsum([self.context.speed * max(p.len for p in s) for s in self.context.sections])
        baseframe = (frameindex // oldsectionends[-1]) * sectionends[-1]
        localframe = frameindex % oldsectionends[-1]
        oldsectionindex = bisect.bisect(oldsectionends, localframe)
        sectionframe = localframe - (oldsectionends[oldsectionindex - 1] if oldsectionindex else 0)
        opcodes = difflib.SequenceMatcher(a = oldsections, b = self.context.sections).get_opcodes()
        @singleton
        def sectionindex():
            for tag, i1, i2, j1, j2 in opcodes:
                if 'equal' == tag and i1 <= oldsectionindex and oldsectionindex < i2:
                    return j1 + oldsectionindex - i1
            for tag, i1, i2, j1, j2 in opcodes:
                if 'insert' == tag and oldsections[oldsectionindex] in self.context.sections[j1:j2]:
                    return j1 + self.context.sections[j1:j2].index(oldsections[oldsectionindex])
        return baseframe + (0 if sectionindex is None else ((sectionends[sectionindex - 1] if sectionindex else 0) + sectionframe))
