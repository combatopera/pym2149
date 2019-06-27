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
from diapyr import types
from diapyr.util import innerclass
from functools import partial

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

class ChipProxy:

    class ChanProxy:

        def __init__(self, chan):
            self._chan = chan

        def _reg(self, reginfo):
            return reginfo(self._chip, self._chan)

    noiseperiod = asprop(lambda chip: chip.noiseperiodreg)

    def __init__(self, chip, chan, chancount, nomclock, tuning, context):
        self._chans = [self.ChanProxy((chan + i) % chancount) for i in range(chancount)]
        self._chip = chip
        self._nomclock = nomclock
        self._tuning = tuning
        self._context = context

    def _reg(self, reginfo):
        return reginfo(self._chip)

    def __getitem__(self, index):
        return self._chans[index]

    def topitch(self, degree):
        scale = self._context.scale >> (1 - self._context.mode)
        return self._context.tonic + float(scale[degree[0] * scale.len + degree[1]] + degree[2])

    def toperiod(self, pitch):
        return self._tuning.freq(pitch).toneperiod(self._nomclock)

for name, prop in dict(
    fixedlevel = asprop(lambda chip, chan: chip.fixedlevels[chan]),
    noiseflag = asprop(lambda chip, chan: chip.noiseflags[chan]),
    toneflag = asprop(lambda chip, chan: chip.toneflags[chan]),
    toneperiod = asprop(lambda chip, chan: chip.toneperiods[chan]),
    # TODO: Use Reg links so that we can read out the same pitch we set.
    tonepitch = asprop(lambda chip, chan: chip.toneperiods[chan], lambda self: self.toperiod, None),
).items():
    setattr(ChipProxy.ChanProxy, name, prop)
    setattr(ChipProxy, name, convenience(name))
del name, prop
ChipProxy.ChanProxy = innerclass(ChipProxy.ChanProxy)

class NoSuchSectionException(Exception): pass

class LiveCodingBridge(Prerecorded):

    @types(Config, Tuning, Context)
    def __init__(self, config, tuning, context):
        self.nomclock = config.nominalclock
        self.loop = not config.ignoreloop
        self.section = config.section
        self.chancount = config.chipchannels
        self.tuning = tuning
        self.context = context

    @property
    def pianorollheight(self):
        return self.context.speed

    def _step(self, chipproxies, speed, section, frame):
        for proxy in chipproxies:
            proxy.fixedlevel = 0 # XXX: Also reset levelmode?
            proxy.noiseflag = False
            proxy.toneflag = False
        for proxy, pattern in zip(chipproxies, section):
            pattern.of(speed)[frame](frame, speed, proxy, pattern.kwargs)

    def _initialframe(self, sectionframecounts):
        frameindex = 0
        if self.section is None:
            return frameindex
        section = getattr(self.context, self.section)
        for s, k in zip(self.context.sections, sectionframecounts):
            if section == s:
                return frameindex
            frameindex += k
        raise NoSuchSectionException(self.section) # FIXME: And stop threads.

    def _sectionframecount(self, section):
        return self.context.speed * max(pattern.len for pattern in section if pattern is not None)

    def frames(self, chip):
        chipproxies = [ChipProxy(chip, chan, self.chancount, self.nomclock, self.tuning, self.context)
                for chan in range(self.chancount)]
        sectionframecounts = [self._sectionframecount(section) for section in self.context.sections]
        frameindex = self._initialframe(sectionframecounts)
        def sectionandframe():
            frame = frameindex
            while True:
                for section, k in zip(self.context.sections, sectionframecounts):
                    if frame < k:
                        return section, frame
                    frame -= k
        while self.loop or frameindex < sum(sectionframecounts):
            frame = partial(self._step, chipproxies, self.context.speed, *sectionandframe())
            frameindex += 1
            yield frame
