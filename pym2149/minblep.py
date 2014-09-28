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

from __future__ import division
import numpy as np, fractions, logging, numba as nb
from nod import BufNode

log = logging.getLogger(__name__)

def round(v):
  return np.int32(v + .5)

class MinBleps:

  minmag = np.exp(-100)

  def __init__(self, naiverate, outrate, scale, cutoff = .475, transition = .05):
    idealscale = naiverate // fractions.gcd(naiverate, outrate)
    if scale is None:
      scale = idealscale
    elif scale != idealscale:
      raise Exception("Expected scale %s but ideal is %s." % (scale, idealscale))
    log.debug('Creating minBLEPs.')
    # XXX: Use kaiser and/or satisfy min transition?
    # Closest even order to 4/transition:
    order = int(round(4 / transition / 2)) * 2
    self.kernelsize = order * scale + 1
    # The fft/ifft are too slow unless size is a power of 2:
    self.size = 2 ** 0
    while self.size < self.kernelsize:
      self.size <<= 1
    self.midpoint = self.size // 2 # Index of peak of sinc.
    x = (np.arange(self.kernelsize) / (self.kernelsize - 1) * 2 - 1) * order * cutoff
    # If cutoff is .5 the sinc starts and ends with zero.
    # The window is necessary for a reliable integral height later:
    self.bli = np.blackman(self.kernelsize) * np.sinc(x) / scale * cutoff * 2
    self.rpad = (self.size - self.kernelsize) // 2 # Observe floor of odd difference.
    self.lpad = 1 + self.rpad
    self.bli = np.concatenate([np.zeros(self.lpad), self.bli, np.zeros(self.rpad)])
    self.blep = np.cumsum(self.bli)
    # Everything is real after we discard the phase info here:
    absdft = np.abs(np.fft.fft(self.bli))
    # The "real cepstrum" is symmetric apart from its first element:
    realcepstrum = np.fft.ifft(np.log(np.maximum(self.minmag, absdft)))
    # Leave first point, zero max phase part, double min phase part to compensate.
    # The midpoint is shared between parts so it doesn't change:
    realcepstrum[1:self.midpoint] *= 2
    realcepstrum[self.midpoint + 1:] = 0
    self.minbli = np.fft.ifft(np.exp(np.fft.fft(realcepstrum))).real
    self.minblep = np.cumsum(self.minbli, dtype = BufNode.floatdtype)
    # Prepend zeros to simplify naivex2outx calc:
    self.minblep = np.append(np.zeros(scale - 1, BufNode.floatdtype), self.minblep)
    # Append ones so that all mixins have the same length:
    ones = (-len(self.minblep)) % scale
    self.minblep = np.append(self.minblep, np.ones(ones, BufNode.floatdtype))
    self.mixinsize = len(self.minblep) // scale
    # The naiverate and outrate will line up at 1 second:
    dualscale = outrate // fractions.gcd(naiverate, outrate)
    nearest = np.arange(naiverate, dtype = np.int32) * dualscale
    self.naivex2outx = nearest // scale
    self.naivex2shape = self.naivex2outx * scale - nearest + scale - 1
    self.demultiplexed = np.empty(self.minblep.shape, dtype = self.minblep.dtype)
    for i in xrange(scale):
      self.demultiplexed[i * self.mixinsize:(i + 1) * self.mixinsize] = self.minblep[i::scale]
    self.naivex2off = self.naivex2shape * self.mixinsize
    log.debug('%s minBLEPs created.', scale)
    self.naiverate = naiverate
    self.outrate = outrate
    self.scale = scale

  def getoutcount(self, naivex, naiven):
    out0 = self.naivex2outx[naivex]
    naivex += naiven
    while naivex >= self.naiverate:
      out0 -= self.outrate
      naivex -= self.naiverate
    # Subtract from the first sample we can't output this block:
    return self.naivex2outx[naivex] - out0

  def paste(self, naivex, diffbuf, outbuf):
    i4 = np.int32
    pasten = i4(len(diffbuf))
    pasteminbleps(pasten, outbuf.buf, self.naivex2outx, i4(len(outbuf)), i4(self.mixinsize), self.demultiplexed, self.naivex2off, diffbuf.buf, i4(self.scale), i4(naivex), i4(self.naiverate), i4(self.outrate))

def pasteminbleps(n, out, naivex2outx, outsize, mixinsize, demultiplexed, naivex2off, amp, scale, naivex, naiverate, outrate):
  pasteminblepsimpl(n, out, naivex2outx, outsize, mixinsize, demultiplexed, naivex2off, amp, scale, naivex, naiverate, outrate)

log.debug('Compiling output stage.')

@nb.jit(nb.void(nb.i4, nb.f4[:], nb.i4[:], nb.i4, nb.i4, nb.f4[:], nb.i4[:], nb.f4[:], nb.i4, nb.i4, nb.i4, nb.i4), nopython = True)
def pasteminblepsimpl(n, out, naivex2outx, outsize, mixinsize, demultiplexed, naivex2off, amp, scale, naivex, naiverate, outrate):
  # TODO: This code needs tests.
  # Naming constants makes inspect_types easier to read:
  zero = 0
  one = 1
  x = zero
  out0 = naivex2outx[naivex]
  while n:
    m = min(n, naiverate - naivex)
    limit = naivex + m
    while naivex < limit:
      a = amp[x]
      if a != zero:
        i = naivex2outx[naivex] - out0
        s = naivex2off[naivex]
        j = i + mixinsize
        if i < j:
          while 1:
            out[i] += demultiplexed[s] * a
            # XXX: Do we really need 2 increments?
            i += one
            s += one
            if i == j:
              break
        if i < outsize:
          while 1:
            out[i] += a
            i += one
            if i == outsize:
              break
      x += one
      naivex += one
    n = n - m
    naivex = zero
    out0 = out0 - outrate

log.debug('Done compiling.')
