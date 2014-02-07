#!/usr/bin/env python

from __future__ import division
import numpy as np
from pym2149.buf import MasterBuf
from pym2149.minblep import MinBleps

def main():
  import subprocess, sys
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
  outmaster = MasterBuf(dtype = dtype)
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
  outbuf = outmaster.ensureandcrop(outsize)
  outbuf.fill(0)
  for ctrlx in np.flatnonzero(diffsignal): # XXX: Can we avoid making a new array?
    outi, mixin = minbleps.getmixin(ctrlx, ctrlrate, outrate, diffsignal[ctrlx], minblepbuf)
    outj = min(outsize, outi + len(mixin.buf))
    outbuf.buf[outi:outj] += mixin.buf[:outj - outi]
    outbuf.buf[outj:] += diffsignal[ctrlx]
  command = ['sox', '-t', 'raw', '-r', str(outrate), '-e', 'float', '-b', '32', '-', 'minbleppoc.wav']
  sox = subprocess.Popen(command, stdin = subprocess.PIPE)
  outbuf.tofile(sox.stdin)
  sox.stdin.close()
  sys.exit(sox.wait())

if __name__ == '__main__':
  main()
