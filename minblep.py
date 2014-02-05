#!/usr/bin/env python

from __future__ import division
import numpy as np, fractions, math

class MinBleps:

  @staticmethod
  def idealscale(ctrlrate, outrate):
    return ctrlrate // fractions.gcd(ctrlrate, outrate)

  def __init__(self, scale, cutoff = .475, transition = .05):
    # Closest even order to 4/transition:
    order = int(round(4 / transition / 2)) * 2
    self.midpoint = order * scale // 2 # Index of peak of sinc.
    self.size = order * scale + 1
    x = (np.arange(self.size) / (self.size - 1) * 2 - 1) * order * cutoff
    # If cutoff is .5 the sinc starts and ends with zero.
    # The window is necessary for a reliable integral height later:
    self.bli = np.blackman(self.size) * np.sinc(x) / scale * cutoff * 2
    self.blep = np.cumsum(self.bli)
    # Everything is real after we discard the phase info here:
    absdft = np.abs(np.fft.fft(self.bli))
    realcepstrum = np.fft.ifft(np.log(absdft)) # Symmetric apart from first element.
    # Leave first point, zero max phase part, double min phase part to compensate:
    realcepstrum[1:self.midpoint + 1] *= 2
    realcepstrum[self.midpoint + 1:] = 0
    self.minbli = np.fft.ifft(np.exp(np.fft.fft(realcepstrum))).real
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

def render():
  import subprocess, sys
  from pym2149.buf import MasterBuf
  ctrlrate = 2000000
  outrate = 44100
  tonefreq = 1500
  toneamp = .25
  scale = 500 # Smaller values result in worse-looking spectrograms.
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
  minbleps = MinBleps(scale)
  diffsignal[:] = ctrlsignal
  diffsignal[0] -= 0 # Last value of previous ctrlsignal.
  diffsignal[1:] -= ctrlsignal[:-1]
  outsignal[:] = 0
  for ctrlx in np.flatnonzero(diffsignal): # XXX: Can we avoid making a new array?
    outi, mixin = minbleps.getmixin(ctrlx, ctrlrate, outrate, diffsignal[ctrlx], minblepbuf)
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
