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

from .pitch import Pitch
from .program import FX, NullNote
from .const import midichannelcount
from .mediation import Mediation
from .iface import Config, Tuning
from .config import ConfigSubscription, ConfigName
from .ym2149 import LogicalRegisters
from diapyr import types, DI
from contextlib import contextmanager
import logging

log = logging.getLogger(__name__)

class ChanNote:

    def __init__(self, onframe, program, nomclock, chip, chipindex, midipair, voladj, fx, normvel, tuning):
        self.program = program
        class TunedPitch(Pitch):
            def freq(self):
                return tuning.freq(self)
        with self._guard():
            self.note = program(nomclock, chip, chipindex, TunedPitch(midipair[1]), voladj, fx, normvel)
        self.onframe = onframe
        self.chip = chip
        self.chipindex = chipindex
        self.midipair = midipair
        self.fx = fx
        self.offframe = None

    def off(self, frame):
        with self._guard():
            self.note.onframes = frame - self.onframe
        self.offframe = frame

    def update(self, frame):
        with self._guard():
            self._update(frame)

    @contextmanager
    def _guard(self):
        program = self.program
        try:
            yield
        except Exception:
            log.exception("%s failed:", program.__name__)
            self.off = self.update = lambda *args: None # Freeze this note.

    def _callnoteon(self):
        if self.program.clean: # XXX: Or go via self.note?
            self.chip.flagsoff(self.chipindex) # Make it so that the impl only has to switch things on.
        self.note.noteon()

    def _update(self, frame):
        if self.offframe is None:
            f = frame - self.onframe
            if not f:
                self._callnoteon()
            self.note.noteonframe(f) # May never be called, so noteoff/noteoffframe should not rely on side-effects.
        else:
            if self.onframe == self.offframe:
                self._callnoteon()
            f = frame - self.offframe
            if not f:
                self.note.noteoff()
            self.note.noteoffframe(f)

class ControlPair:

    def __init__(self, binaryzero, flush, shift):
        self.binary = self.binaryzero = binaryzero
        self.flush = flush
        self.shift = shift

    def install(self, d, msbindex):
        d[msbindex] = self.setmsb
        d[msbindex + 0x20] = self.setlsb

    def setmsb(self, midichan, msb):
        self.binary = (msb << 7) | (self.binary & 0x7f)
        self.flush(midichan, (self.binary - self.binaryzero) >> self.shift)

    def setlsb(self, midichan, lsb):
        self.binary = (self.binary & (0x7f << 7)) | lsb
        self.flush(midichan, (self.binary - self.binaryzero) >> self.shift)

class Channels:

    @classmethod
    def configure(cls, di):
        di.add(cls)
        di.add(ChannelsConfigSubscription)

    @types(Config, LogicalRegisters, Mediation, Tuning)
    def __init__(self, config, chip, mediation, tuning):
        self.nomclock = config.nominalclock
        neutralvel = config.neutralvelocity
        velperlevel = config.velocityperlevel
        self.tovoladj = lambda vel: (vel - neutralvel + velperlevel // 2) // velperlevel
        self.chip = chip
        self.midichantoprogram = dict(config.midichanneltoprogram) # Copy as we will be changing it.
        self.slidemidichans = set(config.slidechannels)
        self.fxfactory = lambda midichan: FX(config, midichan in self.slidemidichans)
        self.midichantofx = {c: self.fxfactory(c) for c in range(config.midichannelbase, config.midichannelbase + midichannelcount)}
        self.mediation = mediation
        self.tuning = tuning
        self.zerovelisnoteoffmidichans = set(config.zerovelocityisnoteoffchannels)
        self.monophonicmidichans = set(config.monophonicchannels)
        self.controllers = {}
        def flush(midichan, value):
            self.midichantofx[midichan].modulation.set(value)
        ControlPair(0, flush, 0).install(self.controllers, 0x01)
        def flush(midichan, value):
            self.midichantofx[midichan].pan.set(value)
        ControlPair(0x2000, flush, 0).install(self.controllers, 0x0a)
        self.prevtext = None
        self.frameindex = 0
        self.channotes = [None] * config.chipchannels
        throwawayfx = self.fxfactory(None)
        for chipchan in range(config.chipchannels):
            self.newnote(NullNote, (None, 60), 0x7f, throwawayfx, chipchan)

    @staticmethod
    def normvel(vel):
        return max(0, (vel - 1) / 0x7e)

    def newnote(self, program, midipair, vel, fx, chipchan):
        self.channotes[chipchan] = ChanNote(self.frameindex, program, self.nomclock, self.chip, chipchan, midipair, self.tovoladj(vel), fx, self.normvel(vel), self.tuning)

    def reconfigure(self, config):
        self.midiprograms = config.midiprograms

    def _getfx(self, midichan):
        try:
            fx = self.midichantofx[midichan]
        except KeyError:
            self.midichantofx[midichan] = fx = self.fxfactory(midichan)
        return fx

    def noteon(self, midichan, midinote, vel):
        if (not vel) and midichan in self.zerovelisnoteoffmidichans: # TODO: This is normal, confirm midi spec.
            return self.noteoff(midichan, midinote, vel)
        if midichan in self.monophonicmidichans:
            for mn in range(0x80): # FIXME LATER: We have microtonal midinotes now.
                self.noteoff(midichan, mn, 0)
        fx = self._getfx(midichan)
        if midichan in self.slidemidichans:
            fx.bend.value = 0 # Leave target and rate as-is. Note race with midi instant pitch bend (fine part 0).
        # XXX: Keep owner program for logging?
        program = self.midiprograms[self.midichantoprogram[midichan]].programformidinote(midinote) # TODO: Friendlier errors.
        chipchan = self.mediation.acquirechipchan(midichan, midinote, self.frameindex)
        self.newnote(program, (midichan, midinote), vel, fx, chipchan)
        return chipchan,

    def noteoff(self, midichan, midinote, vel): # XXX: Use vel?
        chipchan = self.mediation.releasechipchan(midichan, midinote)
        if chipchan is not None:
            channote = self.channotes[chipchan]
            if (midichan, midinote) == channote.midipair:
                channote.off(self.frameindex)
                return chipchan,

    def pitchbend(self, midichan, bend):
        self.midichantofx[midichan].bend.set(bend)

    def controlchange(self, midichan, controller, value):
        if controller in self.controllers:
            self.controllers[controller](midichan, value)

    def programchange(self, midichan, program):
        self.midichantoprogram[midichan] = program

    def updateall(self):
        text = ' | '.join("%s@%s" % (channote.program.__name__, self.mediation.currentmidichans(channote.chipindex)) for channote in self.channotes)
        if text != self.prevtext:
            log.debug(text)
            self.prevtext = text
        for channote in self.channotes:
            channote.update(self.frameindex)

    def closeframe(self):
        for fx in self.midichantofx.values():
            fx.applyrates()
        self.frameindex += 1

    def getpans(self):
        for channote in self.channotes:
            yield channote.fx.normpan()

    def __str__(self):
        return ', '.join("%s -> %s" % (midichan, self.midiprograms[program]) for midichan, program in sorted(self.midichantoprogram.items()))

class ChannelsConfigSubscription(ConfigSubscription):

    @types(Config, ConfigName, DI, Channels)
    def __init__(self, config, configname, di, channels):
        super().__init__(config.profile, configname, di, channels.reconfigure)
