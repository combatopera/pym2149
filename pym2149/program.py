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

from .lfo import LFO, FloatLFO
from .reg import Reg, regproperty
import logging

log = logging.getLogger(__name__)

class FX:

    class SimpleValue:

        def __init__(self, value):
            self.value = value

        def set(self, value):
            self.value = value

        def step(self): pass

    class SlideValue:

        def __init__(self, slidespeed, value):
            self.slidespeed = slidespeed
            self.target = self.value = value

        def set(self, value):
            self.target = value & ~0x7f
            self.rate = (value & 0x7f) * self.slidespeed
            if not self.rate: # Simulate simple behaviour when fine part is 0.
                self.value = self.target

        def step(self):
            if self.value < self.target:
                self.value = min(self.value + self.rate, self.target)
            elif self.value > self.target:
                self.value = max(self.value - self.rate, self.target)

    halfrange = 1 << 13 # Full range is 14 bits.
    minsigned = -halfrange
    maxsigned = halfrange - 1

    @staticmethod
    def signum(n):
        return 1 if n > 0 else (-1 if n < 0 else 0)

    def __init__(self, config, slide):
        self.bendpersemitone = config.pitchbendpersemitone
        if slide:
            slidespeed = config.slidespeed
            valueimpl = lambda v: self.SlideValue(slidespeed, v)
        else:
            valueimpl = self.SimpleValue
        self.bend = valueimpl(0)
        self.modulation = valueimpl(self.halfrange)
        self.pan = valueimpl(0)

    def applyrates(self):
        for v in self.bend, self.modulation, self.pan:
            v.step()

    def bendsemitones(self):
        return self.bend.value / self.bendpersemitone

    def relmodulation(self):
        return (max(1, self.modulation.value) - self.halfrange) / (self.halfrange - 1) / 2 + .5

    def normpan(self):
        # Observe we don't apply maxpan, which is only for the auto-stereo:
        return max(self.minsigned + 1, self.pan.value) / (self.halfrange - 1)

class Unpitched:

    @classmethod
    def programformidinote(cls, midinote):
        return cls.midinotetoprogram.get(midinote, Note) # Observe a miss results in silence.

class Note(Unpitched):

    clean = True
    toneperiod = regproperty(lambda note: note.toneperiodreg)
    toneflag = regproperty(lambda note: note.toneflagreg)
    noiseflag = regproperty(lambda note: note.noiseflagreg)
    fixedlevel = regproperty(lambda note: note.fixedlevelreg)
    levelmode = regproperty(lambda note: note.levelmodereg)
    tonepitch = regproperty(lambda note: note.tonepitchreg)
    tonefreq = regproperty(lambda note: note.tonefreqreg)

    @classmethod
    def programformidinote(cls, midinote):
        return cls

    def __init__(self, nomclock, chip, chipchan, pitch, voladj, fx, normvel):
        self.toneperiodreg = chip.toneperiods[chipchan]
        self.toneflagreg = chip.toneflags[chipchan]
        self.timer = chip.timers[chipchan]
        self.noiseflagreg = chip.noiseflags[chipchan]
        self.fixedlevelreg = Reg()
        # No reverse link, we don't want to pollute the chip with references:
        chip.fixedlevels[chipchan].link(lambda unclamped: max(0, min(15, unclamped)), self.fixedlevelreg)
        self.levelmodereg = chip.levelmodes[chipchan]
        self.tonefreqreg = Reg()
        self.toneperiodreg.link(lambda f: f.toneperiod(nomclock), self.tonefreqreg) # No reverse link.
        self.tonepitchreg = Reg()
        self.tonefreqreg.link(lambda p: (p + fx.bendsemitones()).freq(), self.tonepitchreg)
        self.nomclock = nomclock
        self.chip = chip
        self.chipchan = chipchan
        self.pitch = pitch
        self.voladj = voladj
        self.fx = fx
        self.velocity = normvel

    def noteon(self): pass

    def noteonframe(self, frame):
        "May never be called, so don't make changes that noteoff or a custom impl of noteoffframe later relies on."

    def noteoff(self): pass

    def noteoffframe(self, frame):
        self.noteonframe(self.onframes + frame)

class NullNote(Note):

    clean = False

class DefaultNote(Note): # TODO: Does not belong here.

    vib = FloatLFO(0).hold(10).tri(8, 2, .2).loop(8)
    fadeout = LFO(-1).hold(1).lin(28, -15)

    def noteon(self):
        self.toneflag = True
        self.fixedlevel = 13 + self.voladj

    def noteonframe(self, frame):
        self.tonepitch = self.pitch + self.fx.relmodulation() * self.vib(frame)

    def noteoffframe(self, frame):
        self.tonepitch = self.pitch + self.fx.relmodulation() * self.vib(self.onframes + frame)
        self.fixedlevel = 13 + self.voladj + self.fadeout(frame)
