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

from .util import threadlocals
from ..iface import Config, Prerecorded, Tuning, Context
from ..reg import regproperty, Reg
from ..util import ExceptionCatcher
from ..ym2149 import ClockInfo
from diapyr import types
from diapyr.util import innerclass
from functools import partial
import logging

log = logging.getLogger(__name__)

def _convenience(name):
    def fget(self):
        return getattr(self[0], name)
    def fset(self, value):
        setattr(self[0], name, value)
    return property(fget, fset)

class ChanProxy:

    def __init__(self, chip, chan, clock, tuning):
        self.tonepitchreg = Reg()
        self.tonefreqreg = Reg().link(tuning.freq, self.tonepitchreg)
        self.toneperiodreg = Reg().link(clock.toneperiod, self.tonefreqreg)
        chip.toneperiods[chan].link(round, self.toneperiodreg)
        self.levelreg = Reg()
        chip.fixedlevels[chan].link(lambda l: min(15, max(0, round(l))), self.levelreg)
        self._chip = chip
        self._chan = chan

class ChipRegs:

    def __init__(self, chip, clock, tuning):
        self.noisefreqreg = Reg()
        self.noiseperiodreg = Reg().link(clock.noiseperiod, self.noisefreqreg)
        chip.noiseperiod.link(round, self.noiseperiodreg)
        self.envpitchreg = Reg()
        self.envfreqreg = Reg().link(tuning.freq, self.envpitchreg)
        self.envperiodreg = Reg().link(lambda f, s: clock.envperiod(f, s), self.envfreqreg, chip.envshape)
        chip.envperiod.link(round, self.envperiodreg)

class ChipProxy(ExceptionCatcher):

    noiseperiod = regproperty(lambda self: self._chipregs.noiseperiodreg)
    envshape = regproperty(lambda self: self._chip.envshape)
    envperiod = regproperty(lambda self: self._chipregs.envperiodreg)
    envpitch = regproperty(lambda self: self._chipregs.envpitchreg)
    noisefreq = regproperty(lambda self: self._chipregs.noisefreqreg)
    envfreq = regproperty(lambda self: self._chipregs.envfreqreg)

    def __init__(self, chip, chan, chanproxies, chipregs):
        self._letter = chr(ord('A') + chan)
        self._chip = chip
        self._chans = chanproxies
        self._chipregs = chipregs

    def __getitem__(self, index):
        return self._chans[index]

    def noisepriority(self):
        return not any(chan.noiseflag for chan in self[1:])

for name, prop in dict(
    tonefreq = regproperty(lambda self: self.tonefreqreg),
    level = regproperty(lambda self: self.levelreg),
    noiseflag = regproperty(lambda self: self._chip.noiseflags[self._chan]),
    toneflag = regproperty(lambda self: self._chip.toneflags[self._chan]),
    toneperiod = regproperty(lambda self: self.toneperiodreg),
    tonepitch = regproperty(lambda self: self.tonepitchreg),
    envflag = regproperty(lambda self: self._chip.levelmodes[self._chan]),
).items():
    setattr(ChanProxy, name, prop)
    setattr(ChipProxy, name, _convenience(name))
del name, prop

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
            chanproxies = 2 * [ChanProxy(chip, chan, self.clock, self.tuning) for chan in range(self.chancount)]
            self.chipproxies = [ChipProxy(chip, chan, chanproxies[chan:self.chancount + chan], chipregs)
                    for chan in range(self.chancount)]

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

    def _initialframe(self):
        frameindex = 0
        if self.sectionname is None:
            return frameindex
        section = getattr(self.context, self.sectionname)
        for s, k in zip(self.context.sections, self.context.sectionframecounts):
            if section == s:
                return frameindex
            frameindex += k
        raise NoSuchSectionException(self.sectionname)

    def _sectionandframe(self, frame):
        while True:
            for section, k in zip(self.context.sections, self.context.sectionframecounts):
                if frame < k:
                    return section, frame
                frame -= k

    def frames(self, chip):
        session = self.Session(chip)
        frameindex = self._initialframe() + self.bias
        with threadlocals(context = self.context):
            while self.loop or frameindex < self.context.totalframecount:
                oldspeed = self.context.speed
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
                # TODO: Adjust frameindex when sections changed.
