#!/usr/bin/env python

from __future__ import division
import numpy as np
from pym2149.buf import MasterBuf
from pym2149.minblep import MinBleps

def main():
  import subprocess, sys
  naiverate = 2000000
  outrate = 44100
  tonefreq = 1500
  toneamp = .25
  scale = 500 # Smaller values result in worse-looking spectrograms.
  naivesize = naiverate
  outsize = outrate
  dtype = np.float32
  toneoscscale = 16
  periodreg = int(round(naiverate / (toneoscscale * tonefreq)))
  period = toneoscscale * periodreg
  naivemaster = MasterBuf(dtype = dtype)
  diffmaster = MasterBuf(dtype = dtype)
  outmaster = MasterBuf(dtype = dtype)
  minblepbuf = MasterBuf(dtype = dtype)
  naivebuf = naivemaster.ensureandcrop(naivesize)
  x = 0
  while x < naivesize:
    naivebuf.fillpart(x, x + period // 2, toneamp)
    naivebuf.fillpart(x + period // 2, x + period, -toneamp)
    x += period
  minbleps = MinBleps(scale)
  diffbuf = diffmaster.ensureandcrop(naivesize)
  diffbuf.copybuf(naivebuf)
  diffbuf.buf[0] -= 0 # Last value of previous naivesignal.
  diffbuf.buf[1:] -= naivebuf.buf[:-1]
  outbuf = outmaster.ensureandcrop(outsize)
  outbuf.fill(0)
  for naivex in np.flatnonzero(diffbuf.buf): # XXX: Can we avoid making a new array?
    outi, mixin = minbleps.getmixin(naivex, naiverate, outrate, diffbuf.buf[naivex], minblepbuf)
    outj = min(outsize, outi + len(mixin.buf))
    outbuf.buf[outi:outj] += mixin.buf[:outj - outi]
    outbuf.buf[outj:] += diffbuf.buf[naivex]
  command = ['sox', '-t', 'raw', '-r', str(outrate), '-e', 'float', '-b', '32', '-', 'minbleppoc.wav']
  sox = subprocess.Popen(command, stdin = subprocess.PIPE)
  outbuf.tofile(sox.stdin)
  sox.stdin.close()
  sys.exit(sox.wait())

if __name__ == '__main__':
  main()
