#!/usr/bin/env python

from __future__ import division
import numpy as np, logging, fractions, math

log = logging.getLogger(__name__)

class MinBlep:

  @staticmethod
  def idealscale(ctrlrate, outrate):
    return ctrlrate // fractions.gcd(ctrlrate, outrate)

  def __init__(self, zeros, scale):
    # TODO: Rename vars for consistency with the detailed paper.
    # FIXME: Instead of zeros take transition band params.
    self.midpoint = zeros * scale # Index of peak of sinc.
    self.size = self.midpoint * 2 + 1
    x = 2 * zeros * np.arange(self.size) / (self.size - 1) - zeros
    # The sinc starts and ends with zero, and the window fixes the integral height:
    self.bli = np.blackman(self.size) * np.sinc(x) / scale
    self.blep = np.cumsum(self.bli)
    # Everything is real after we discard the phase info here:
    absdft = np.abs(np.fft.fft(self.bli))
    realcepstrum = np.fft.ifft(np.log(absdft)) # Symmetric apart from first element.
    # Leave first point, zero max phase part, double min phase part to compensate:
    realcepstrum[1:self.midpoint + 1] *= 2
    realcepstrum[self.midpoint + 1:] = 0
    self.minbli = np.fft.ifft(np.exp(np.fft.fft(realcepstrum))).real
    # Check our cepstrum manipulation isn't broken. TODO: Replace with unit test.
    if not np.allclose(absdft, np.abs(np.fft.fft(self.minbli))):
      log.warn('Bad min-phase reconstruction.')
    self.minblep = np.cumsum(self.minbli)
    self.scale = scale

  def getmixin(self, ctrlx, ctrlrate, outrate, amp, buf):
    outx = ctrlx / ctrlrate * outrate # 0, 0+, .5, 1-, 1
    outi = int(math.ceil(outx)) # 0, 1, 1, 1, 1
    frac = outi - outx # 0, 1-, .5, 0+, 0
    shape = int(round(frac * self.scale)) # XXX: Is round correct here?
    view = self.minblep[shape::self.scale] # Two possible sizes.
    buf = buf.ensureandcrop(len(view))
    buf.buf[:] = view
    buf.buf *= amp
    return outi, buf

def plot():
  import matplotlib.pyplot as plt
  minblep = MinBlep(10, 5)
  plt.plot(minblep.bli * minblep.scale, 'b+')
  plt.plot(minblep.blep, 'bo')
  plt.plot(np.arange(minblep.size) + minblep.midpoint, minblep.minbli * minblep.scale, 'r+')
  for style in 'r', 'ro':
    plt.plot(np.arange(minblep.size) + minblep.midpoint, minblep.minblep, style)
  plt.grid(True)
  plt.show()

def render():
  import subprocess, sys, fractions
  from pym2149.buf import MasterBuf
  ctrlrate = 2000000
  outrate = 44100
  tonefreq = 1500
  toneamp = .25
  scale = 500 # TODO: Find out what we can get away with.
  ctrlsize = ctrlrate
  outsize = outrate
  dtype = np.float32
  toneoscscale = 16
  periodreg = int(round(ctrlrate / (toneoscscale * tonefreq)))
  period = toneoscscale * periodreg
  ctrlsignal = np.empty(ctrlsize, dtype = dtype)
  diffsignal = np.empty(ctrlsize, dtype = dtype)
  outsignal = np.empty(outsize, dtype = dtype)
  minblepbuf = MasterBuf(dtype = dtype)
  x = 0
  while x < ctrlsize:
    ctrlsignal[x:x + period // 2] = toneamp
    ctrlsignal[x + period // 2:x + period] = -toneamp
    x += period
  minblep = MinBlep(40, scale)
  diffsignal[:] = ctrlsignal
  diffsignal[0] -= 0 # Last value of previous ctrlsignal.
  diffsignal[1:] -= ctrlsignal[:-1]
  outsignal[:] = 0
  for ctrlx in np.flatnonzero(diffsignal): # XXX: Can we avoid making a new array?
    outi, mixin = minblep.getmixin(ctrlx, ctrlrate, outrate, diffsignal[ctrlx], minblepbuf)
    outj = min(outsize, outi + len(mixin.buf))
    outsignal[outi:outj] += mixin.buf[:outj - outi]
    outsignal[outj:] += diffsignal[ctrlx]
  command = ['sox', '-t', 'raw', '-r', str(outrate), '-e', 'float', '-b', '32', '-', 'minblep.wav']
  sox = subprocess.Popen(command, stdin = subprocess.PIPE)
  outsignal.tofile(sox.stdin)
  sox.stdin.close()
  sys.exit(sox.wait())

if __name__ == '__main__':
  render()
