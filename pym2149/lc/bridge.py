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

from ..iface import Config, Prerecorded, Tuning, Context
from ..util import ExceptionCatcher
from diapyr import types
from diapyr.util import innerclass
from functools import partial
import logging

log = logging.getLogger(__name__)

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

        def __init__(self, chan):
            self._chan = chan

        def _reg(self, reginfo):
            return reginfo(self._chip, self._chan)

    noiseperiod = asprop(lambda chip: chip.noiseperiodreg)
    envshape = asprop(lambda chip: chip.envshapereg)
    envperiod = asprop(lambda chip: chip.envperiodreg)

    def __init__(self, chip, chan, chancount, nomclock, tuning, context):
        self._chans = [self.ChanProxy((chan + i) % chancount) for i in range(chancount)]
        self._letter = chr(ord('A') + chan)
        self._chip = chip
        self._nomclock = nomclock
        self._tuning = tuning
        self._context = context

    def _reg(self, reginfo):
        return reginfo(self._chip)

    def __getitem__(self, index):
        return self._chans[index]

    def noisepriority(self):
        return not any(chan.noiseflag for chan in self[1:])

    def topitch(self, degree):
        scale = self._context.scale >> (1 - self._context.mode)
        return self._context.tonic + float(scale[degree[0] * scale.len + degree[1]] + degree[2])

    def toperiod(self, pitch):
        return self._tuning.freq(pitch).toneperiod(self._nomclock)

    def toenvperiod(self, pitch):
        return self._tuning.freq(pitch).envperiod(self._nomclock, self.envshape)

for name, prop in dict(
    fixedlevel = asprop(lambda chip, chan: chip.fixedlevels[chan]),
    noiseflag = asprop(lambda chip, chan: chip.noiseflags[chan]),
    toneflag = asprop(lambda chip, chan: chip.toneflags[chan]),
    toneperiod = asprop(lambda chip, chan: chip.toneperiods[chan]),
    # TODO: Use Reg links so that we can read out an unrounded period for example.
    tonepitch = asprop(lambda chip, chan: chip.toneperiods[chan], lambda self: self.toperiod, None),
    envflag = asprop(lambda chip, chan: chip.levelmodes[chan]),
).items():
    setattr(ChipProxy.ChanProxy, name, prop)
    setattr(ChipProxy, name, convenience(name))
del name, prop
ChipProxy.ChanProxy = innerclass(ChipProxy.ChanProxy)

class NoSuchSectionException(Exception): pass

class LiveCodingBridge(Prerecorded):

    bias = .5 # TODO: Make configurable for predictable swing in odd speed case.

    @types(Config, Tuning, Context)
    def __init__(self, config, tuning, context):
        self.nomclock = config.nominalclock
        self.loop = not config.ignoreloop
        self.sectionname = config.section
        self.chancount = config.chipchannels
        self.tuning = tuning
        self.context = context

    @property
    def pianorollheight(self):
        return self.context.speed

    @innerclass
    class Session(ExceptionCatcher):

        def __init__(self, chip):
            self.chipproxies = [ChipProxy(chip, chan, self.chancount, self.nomclock, self.tuning, self.context)
                    for chan in range(self.chancount)]

        def _quiet(self):
            for proxy in self.chipproxies:
                proxy.envflag = False
                proxy.fixedlevel = 0
                proxy.noiseflag = False
                proxy.toneflag = False

        def _step(self, speed, section, frame):
            self._quiet()
            for proxy, pattern in zip(self.chipproxies, section):
                with proxy.catch("Channel %s update failed:", proxy._letter):
                    pattern.apply(speed, frame, proxy, self.context)

    def _initialframe(self):
        frameindex = 0
        if self.sectionname is None:
            return frameindex
        section = getattr(self.context, self.sectionname)
        for s, k in zip(self.context.sections, self.context.sectionframecounts):
            if section == s:
                return frameindex
            frameindex += k
        raise NoSuchSectionException(self.sectionname) # FIXME: And stop threads.

    def _sectionandframe(self, frame):
        while True:
            for section, k in zip(self.context.sections, self.context.sectionframecounts):
                if frame < k:
                    return section, frame
                frame -= k

    def frames(self, chip):
        session = self.Session(chip)
        frameindex = self._initialframe() + self.bias
        while self.loop or frameindex < self.context.totalframecount:
            frame = session._quiet
            if self.context.totalframecount: # Otherwise freeze until there is something to play.
                with session.catch('Failed to prepare a frame:'):
                    frame = partial(session._step, self.context.speed, *self._sectionandframe(frameindex))
                    frameindex += 1
            frame()
            yield
            oldspeed = self.context.speed
            self.context._flip()
            if oldspeed != self.context.speed:
                # FIXME: This also needs to happen when speed changed programmatically.
                frameindex = (frameindex - self.bias) / oldspeed * self.context.speed + self.bias
