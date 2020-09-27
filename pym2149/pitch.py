# Copyright 2014, 2018, 2019, 2020 Andrzej Cichocki

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

from .iface import Config, Tuning
from diapyr import DI, types
from lurlene.context import Context
import bisect, logging, math

log = logging.getLogger(__name__)

class ContextTuning(Tuning):

    @types(Context, DI)
    def __init__(self, context, di):
        self.context = context
        self.di = di

    def __getattr__(self, name):
        return getattr(self.di(self.context.get('tuning')), name)

    def dispose(self):
        pass

class EqualTemperament:

    @types(Config)
    def __init__(self, config):
        self.reffreq = float(config.referencefrequency)
        self.refmidi = float(config.referencemidinote)

    def freq(self, pitch):
        return self.reffreq * 2 ** ((pitch - self.refmidi) / 12)

    def pitch(self, freq):
        return Pitch(self.refmidi + 12 * math.log(freq / self.reffreq, 2))

class Unequal:

    def __init__(self, refpitch, freqs):
        self.factors = [math.log(g / f, 2) for f, g in zip(freqs, freqs[1:] + [freqs[0] * 2])]
        self.refpitch = refpitch
        self.freqs = freqs

    def freq(self, pitch):
        pitch -= self.refpitch
        pitchindex = math.floor(pitch) % 12
        return self.freqs[pitchindex] * 2 ** (self.factors[pitchindex] * (pitch % 1) + pitch // 12)

    def pitch(self, freq):
        octave = math.floor(math.log(freq / self.freqs[0], 2))
        freq /= 2 ** octave
        pitchindex = bisect.bisect(self.freqs, freq) - 1 # FIXME LATER: Handle out of range.
        x = math.log(freq / self.freqs[pitchindex], 2) / self.factors[pitchindex]
        return Pitch(self.refpitch + octave * 12 + pitchindex + x)

class Meantone(Unequal):
    'Including Pythagorean as a special case when meantonecomma is zero.'

    syntonic = 81 / 80

    @types(Config)
    def __init__(self, config):
        reffreq = float(config.referencefrequency)
        refpitch = float(config.referencemidinote)
        flats = config.meantoneflats
        fifthratio = 1.5 / self.syntonic ** float(config.meantonecomma)
        freqs = [None] * 12
        for fifth in range(-flats, 12 - flats):
            pitch = fifth * 7
            freqs[pitch % 12] = reffreq * fifthratio ** fifth / 2 ** (pitch // 12)
        super().__init__(refpitch, freqs)
        wolfpitch = Pitch(refpitch + 11 - flats)
        log.debug("The fifth %s to %s is a wolf interval.", wolfpitch, wolfpitch + 7)

class FiveLimit(Unequal):
    'Asymmetric variant.'

    @types(Config)
    def __init__(self, config):
        reffreq = float(config.referencefrequency)
        refpitch = float(config.referencemidinote)
        freqs = [None] * 12
        for p5 in range(-1, 2):
            for p3 in range(-1, 3): # Skip first column for asymmetric.
                ratio = 3 ** p3 * 5 ** p5
                ratio /= 2 ** math.floor(math.log(ratio, 2))
                index = round(math.log(ratio, 2) * 12)
                freqs[index] = reffreq * ratio
        super().__init__(refpitch, freqs)

def configure(di):
    di.add(ContextTuning)
    di.add(EqualTemperament)
    di.add(Meantone)
    di.add(FiveLimit)

class Pitch(float):

    names = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')

    def __add__(self, that):
        return type(self)(float.__add__(self, that))

    def __sub__(self, that):
        return type(self)(float.__sub__(self, that))

    def __str__(self):
        return self.str(10)

    def str(self, mincents):
        nearest = int(math.ceil(self - .5))
        octave = nearest // 12
        note = nearest % 12
        cents = int(round((self - nearest) * 100))
        octave -= 1
        notestr = self.names[note]
        if len(notestr) < 2:
            notestr += '.'
        octavestr = str(octave)
        if len(octavestr) < 2:
            octavestr = '.' + octavestr
        if abs(cents) < mincents:
            centsstr = ' ' * 3
        else:
            centsstr = "%+3d" % cents
        return notestr + octavestr + centsstr
