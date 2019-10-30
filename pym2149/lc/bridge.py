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

# TODO: Use Reg links so that we can read out an unrounded period for example.
def asprop(reginfo, enc = lambda self: round, dec = lambda self: lambda x: x):
    def fget(self):
        return dec(self)(self._reg(reginfo).value)
    def fset(self, value):
        self._reg(reginfo).value = enc(self)(value)
    return property(fget, fset)

def convenience(name):
    def fget(self):
        return getattr(self[0], name)
    def fset(self, value):
        setattr(self[0], name, value)
    return property(fget, fset)

class ChipProxy(ExceptionCatcher):

    class ChanProxy:

        def __init__(self, chan, clock, tuning):
            self.tonepitchreg = Reg()
            self.tonefreqreg = Reg().link(tuning.freq, self.tonepitchreg)
            self._chip.toneperiods[chan].link(lambda f: round(clock.toneperiod(f)), self.tonefreqreg)
            self.levelreg = Reg()
            self._chip.fixedlevels[chan].link(lambda l: min(15, max(0, round(l))), self.levelreg)
            self._chan = chan

        def _reg(self, reginfo):
            return reginfo(self._chip, self._chan)

    noiseperiod = asprop(lambda chip: chip.noiseperiod)
    envshape = asprop(lambda chip: chip.envshape)
    envperiod = asprop(lambda chip: chip.envperiod)
    envpitch = regproperty(lambda self: self.envpitchreg)
    noisefreq = regproperty(lambda self: self.noisefreqreg)
    envfreq = regproperty(lambda self: self.envfreqreg)

    def __init__(self, chip, chan, chancount, clock, tuning, context):
        self.noisefreqreg = Reg()
        chip.noiseperiod.link(lambda f: round(clock.noiseperiod(f)), self.noisefreqreg)
        self.envpitchreg = Reg()
        self.envfreqreg = Reg().link(tuning.freq, self.envpitchreg)
        chip.envperiod.link(lambda f, s: round(clock.envperiod(f, s)), self.envfreqreg, chip.envshape)
        self._chip = chip
        self._chans = [self.ChanProxy((chan + i) % chancount, clock, tuning) for i in range(chancount)]
        self._letter = chr(ord('A') + chan)

    def _reg(self, reginfo):
        return reginfo(self._chip)

    def __getitem__(self, index):
        return self._chans[index]

    def noisepriority(self):
        return not any(chan.noiseflag for chan in self[1:])

for name, prop in dict(
    tonefreq = regproperty(lambda self: self.tonefreqreg),
    level = regproperty(lambda self: self.levelreg),
    noiseflag = regproperty(lambda self: self._chip.noiseflags[self._chan]),
    toneflag = regproperty(lambda self: self._chip.toneflags[self._chan]),
    toneperiod = asprop(lambda chip, chan: chip.toneperiods[chan]),
    tonepitch = regproperty(lambda self: self.tonepitchreg),
    envflag = regproperty(lambda self: self._chip.levelmodes[self._chan]),
).items():
    setattr(ChipProxy.ChanProxy, name, prop)
    setattr(ChipProxy, name, convenience(name))
del name, prop
ChipProxy.ChanProxy = innerclass(ChipProxy.ChanProxy)

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
            self.chipproxies = [ChipProxy(chip, chan, self.chancount, self.clock, self.tuning, self.context)
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
