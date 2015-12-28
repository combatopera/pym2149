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
import numpy as np, fractions, logging, sys, os, cPickle as pickle
from unroll import importunrolled
from diapyr import types
from iface import Config
from ym2149 import ClockInfo
from ring import floatdtype

log = logging.getLogger(__name__)

class MinBleps:

  defaultcutoff = .475
  defaulttransition = .05
  minmag = np.exp(-100)

  @staticmethod
  def round(v):
    return np.int32(v + .5)

  @staticmethod
  def resolvescale(naiverate, outrate, scaleornone):
    idealscale = naiverate // fractions.gcd(naiverate, outrate)
    if scaleornone is not None and scaleornone != idealscale:
      raise Exception("Expected scale %s but ideal is %s." % (scaleornone, idealscale))
    return idealscale

  @staticmethod
  def minrepr(n):
    # Note int will return a long if the value is really too big for int:
    return repr(int(n) if isinstance(n, long) else n)

  @classmethod
  def loadorcreate(cls, naiverate, outrate, scaleornone, cutoff = defaultcutoff, transition = defaulttransition):
    scale = cls.resolvescale(naiverate, outrate, scaleornone)
    name = "%s(%s)" % (cls.__name__, ','.join(map(cls.minrepr, [naiverate, outrate, scale, cutoff, transition])))
    path = os.path.join(os.path.dirname(__file__), name)
    if os.path.exists(path):
      log.debug("Loading cached minBLEPs: %s", path)
      f = open(path, 'rb')
      try:
        minbleps = pickle.load(f)
      finally:
        f.close()
      log.debug("Cached minBLEPs loaded.")
    else:
      minbleps = cls(naiverate, outrate, scale, cutoff, transition)
      parent = os.path.dirname(path)
      if not os.path.exists(parent):
        os.makedirs(parent)
      f = open(path, 'wb')
      try:
        pickle.dump(minbleps, f, pickle.HIGHEST_PROTOCOL)
        f.flush()
      finally:
        f.close()
    return minbleps.link()

  @classmethod
  def create(cls, naiverate, outrate, scaleornone, cutoff = defaultcutoff, transition = defaulttransition):
    return cls(naiverate, outrate, cls.resolvescale(naiverate, outrate, scaleornone), cutoff, transition).link()

  def __init__(self, naiverate, outrate, scale, cutoff, transition):
    log.debug('Creating minBLEPs.')
    # XXX: Use kaiser and/or satisfy min transition?
    # Closest even order to 4/transition:
    order = int(self.round(4 / transition / 2)) * 2
    kernelsize = order * scale + 1
    # The fft/ifft are too slow unless size is a power of 2:
    size = 2 ** 0
    while size < kernelsize:
      size <<= 1
    midpoint = size // 2 # Index of peak of sinc.
    x = (np.arange(kernelsize) / (kernelsize - 1) * 2 - 1) * order * cutoff
    # If cutoff is .5 the sinc starts and ends with zero.
    # The window is necessary for a reliable integral height later:
    self.bli = np.blackman(kernelsize) * np.sinc(x) / scale * cutoff * 2
    rpad = (size - kernelsize) // 2 # Observe floor of odd difference.
    lpad = 1 + rpad
    self.bli = np.concatenate([np.zeros(lpad), self.bli, np.zeros(rpad)])
    # Everything is real after we discard the phase info here:
    absdft = np.abs(np.fft.fft(self.bli))
    # The "real cepstrum" is symmetric apart from its first element:
    realcepstrum = np.fft.ifft(np.log(np.maximum(self.minmag, absdft)))
    # Leave first point, zero max phase part, double min phase part to compensate.
    # The midpoint is shared between parts so it doesn't change:
    realcepstrum[1:midpoint] *= 2
    realcepstrum[midpoint + 1:] = 0
    self.minbli = np.fft.ifft(np.exp(np.fft.fft(realcepstrum))).real
    self.minblep = np.cumsum(self.minbli, dtype = floatdtype)
    # Prepend zeros to simplify naivex2outx calc:
    self.minblep = np.append(np.zeros(scale - 1, floatdtype), self.minblep)
    # Append ones so that all mixins have the same length:
    ones = (-len(self.minblep)) % scale
    self.minblep = np.append(self.minblep, np.ones(ones, floatdtype))
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
    self.outx2minnaivex = np.empty(outrate, dtype = self.naivex2outx.dtype)
    for naivex in xrange(naiverate - 1, -1, -1):
      self.outx2minnaivex[self.naivex2outx[naivex]] = naivex
    log.debug('%s minBLEPs created.', scale)
    self.naiverate = naiverate
    self.outrate = outrate

  def getoutcount(self, naivex, naiven):
    out0 = self.naivex2outx[naivex]
    naivex += naiven
    shift = naivex // self.naiverate
    out0 -= self.outrate * shift
    naivex -= self.naiverate * shift
    # Subtract from the first sample we can't output this block:
    return self.naivex2outx[naivex] - out0

  def getminnaiven(self, naivex, outcount):
    outx = self.naivex2outx[naivex] + outcount
    shift = outx // self.outrate
    outx -= self.outrate * shift
    naivex -= self.naiverate * shift
    return self.outx2minnaivex[outx] - naivex

  def link(self):
    fromfqname = ''.join(w + '.' for w in __name__.split('.')[:-1]) + 'cpaste'
    fqmodulename = fromfqname + str(self.mixinsize)
    if fqmodulename not in sys.modules:
      rootdir = os.path.join(*([os.path.dirname(__file__)] + (len(__name__.split('.')) - 1) * ['..']))
      importunrolled(rootdir, fromfqname, fqmodulename, dict(gmixinsize = self.mixinsize))
    self.pasteminbleps = sys.modules[fqmodulename].pasteminbleps
    return self

  def paste(self, naivex, diffbuf, outbuf):
    self.pasteminbleps(len(diffbuf), outbuf.buf, self.naivex2outx, len(outbuf), self.demultiplexed, self.naivex2off, diffbuf.buf, naivex, self.naiverate, self.outrate)

@types(Config, ClockInfo, this = MinBleps)
def loadorcreate(config, clockinfo):
    return MinBleps.loadorcreate(clockinfo.implclock, config.outputrate, None)
