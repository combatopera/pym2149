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

from .iface import Config, Platform, YMFile
from diapyr import types
import logging

log = logging.getLogger(__name__)
stclock = 2000000
spectrum128crystal = 17734470 # Correct according to service manual.
spectrumclock = spectrum128crystal // 10
defaultscale = 8

class ClockInfo:

    trishapes = frozenset([0xa, 0xe])
    tonescale = 16

    @classmethod
    def _shapescale(cls, shape):
        # Musically, the triangular shapes have twice the scale:
        return 512 if shape in cls.trishapes else 256

    @types(Config, Platform, YMFile)
    def __init__(self, config, platform, ymfile = None):
        self.nomclock = config.nominalclock
        if self.nomclock % config.underclock:
            raise Exception("Clock %s not divisible by underclock %s." % (self.nomclock, config.underclock))
        self.implclock = self.nomclock // config.underclock
        if ymfile is not None and self.nomclock != ymfile.nominalclock:
            log.info("Context clock %s overridden to: %s", ymfile.nominalclock, self.nomclock)
        if self.implclock != self.nomclock:
            log.debug("Clock adjusted to %s to take advantage of non-trivial underclock.", self.implclock)
        if config.underclock < 1 or defaultscale % config.underclock:
            raise Exception("underclock must be a factor of %s." % defaultscale)
        self.scale = defaultscale // config.underclock
        if config.freqclamp:
            # The 0 case just means that 1 is audible:
            self.mintoneperiod = max(1, self._toneperiodclampor0(platform.outputrate))
            log.debug("Minimum tone period: %s", self.mintoneperiod)
        else:
            self.mintoneperiod = 1

    def _toneperiodclampor0(self, outrate):
        # Largest period with frequency strictly greater than Nyquist, or 0 if there isn't one:
        return (self.implclock - 1) // (self.scale * outrate)

    def _convert(self, freqorperiod, scale):
        return self.nomclock / (scale * freqorperiod)

    def toneperiod(self, freq):
        return self._convert(freq, self.tonescale)

    def noiseperiod(self, freq):
        return self._convert(freq, 16) # First notch at freq.

    def envperiod(self, freq, shape):
        return self._convert(freq, self._shapescale(shape))

    def tonefreq(self, period):
        return self._convert(period, self.tonescale)

    def envfreq(self, period, shape):
        return self._convert(period, self._shapescale(shape))
