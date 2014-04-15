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

  def __init__(self, ctrlrate, outrate, scale, cutoff = .475, transition = .05):
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
    # Prepend zeros to simplify outi calc:
    self.minblep = np.append(np.zeros(scale - 1, BufNode.floatdtype), self.minblep)
    # Append ones so that all mixins have the same length:
    ones = (-len(self.minblep)) % scale
    self.minblep = np.append(self.minblep, np.ones(ones, BufNode.floatdtype))
    self.mixinsize = len(self.minblep) // scale
    self.idealscale = ctrlrate // fractions.gcd(ctrlrate, outrate)
    # The ctrlrate and outrate will line up at 1 second:
    nearest = round(np.arange(ctrlrate) / ctrlrate * outrate * scale)
    self.outi = nearest // scale
    self.shape = self.outi * scale - nearest + scale - 1
    log.debug('%s minBLEPs created.', scale)
    self.ctrlrate = ctrlrate
    self.outrate = outrate
    self.scale = scale

  def loadoutindexandshape(self, ctrlx, outi, shape):
    k = ctrlx % self.ctrlrate
    q = ctrlx // self.ctrlrate
    outi.buf[:] = q
    outi.buf[:] *= self.outrate
    outi.buf[:] += self.outi[k]
    shape.buf[:] = self.shape[k]

  def getoutindexandshape(self, ctrlx):
    k = ctrlx % self.ctrlrate
    q = ctrlx // self.ctrlrate
    return q * self.outrate + self.outi[k], self.shape[k]

  def paste(self, ctrlx, out0, diffbuf, outimaster, shapemaster, outbuf):
    nonzeros = diffbuf.nonzeros()
    indexdtype = np.int32
    pasten = indexdtype(len(nonzeros))
    outibuf = outimaster.ensureandcrop(pasten)
    shapebuf = shapemaster.ensureandcrop(pasten)
    self.loadoutindexandshape(ctrlx + nonzeros, outibuf, shapebuf)
    outibuf.buf -= out0
    pasteminbleps(pasten, outbuf.buf, outibuf.buf, indexdtype(len(outbuf)), indexdtype(self.mixinsize), self.minblep, shapebuf.buf, diffbuf.buf[nonzeros], indexdtype(self.scale))

def pasteminbleps(n, out, outi, outsize, mixinsize, minblep, shape, amp, scale):
  pasteminblepsimpl(n, out, outi, outsize, mixinsize, minblep, shape, amp, scale)

log.debug('Compiling output stage.')

@nb.jit(nb.void(nb.i4, nb.f4[:], nb.i4[:], nb.i4, nb.i4, nb.f4[:], nb.i4[:], nb.f4[:], nb.i4), nopython = True)
def pasteminblepsimpl(n, out, outi, outsize, mixinsize, minblep, shape, amp, scale):
  x = 0
  one = 1 # Makes inspect_types easier to read.
  while x < n:
    i = outi[x]
    s = shape[x]
    j = i + mixinsize
    a = amp[x]
    if i < j:
      while 1:
        out[i] += minblep[s] * a
        i += one
        s += scale
        if i == j:
          break
    if i < outsize:
      while 1:
        out[i] += a
        i += one
        if i == outsize:
          break
    x += one

log.debug('Done compiling.')
