#!/usr/bin/env python

from __future__ import division
import numpy as np, random
from pym2149.buf import MasterBuf, Buf
from pym2149.minblep import MinBleps

def main():
  import subprocess, sys
  naiverate = 2000000
  outrate = 44100
  tonefreq = 1500
  toneamp = .25
  scale = 500 # Smaller values result in worse-looking spectrograms.
  naivesize = naiverate # One second of data.
  dtype = np.float32 # Effectively about 24 bits.
  toneoscscale = 16 # A property of the chip.
  periodreg = int(round(naiverate / (toneoscscale * tonefreq)))
  period = toneoscscale * periodreg # Even.
  diffmaster = MasterBuf(dtype = dtype)
  outmaster = MasterBuf(dtype = dtype)
  mixinmaster = MasterBuf(dtype = dtype)
  naivebuf = Buf(np.empty(naivesize, dtype = dtype))
  x = 0
  while x < naivesize:
    naivebuf.fillpart(x, x + period // 2, toneamp)
    naivebuf.fillpart(x + period // 2, x + period, -toneamp)
    x += period
  minbleps = MinBleps(scale)
  overflowsize = minbleps.maxmixinsize() - 1 # Sufficient for any mixin at last sample.
  carrybuf = Buf(np.empty(overflowsize, dtype = dtype))
  # XXX: Can we use numpy to avoid sox altogether?
  command = ['sox', '-t', 'raw', '-r', str(outrate), '-e', 'float', '-b', '32', '-', 'minbleppoc.wav']
  sox = subprocess.Popen(command, stdin = subprocess.PIPE)
  naivex = 0
  dc = 0 # Last naive value of previous block.
  outz = 0 # Absolute index of first output sample being processed in this iteration.
  carrybuf.fill(dc) # Initial carry can be the initial dc level.
  while naivex < naivesize:
    blocksize = random.randint(1, 30000)
    block = Buf(naivebuf.buf[naivex:naivex + blocksize])
    diffbuf = diffmaster.differentiate(dc, block)
    out0 = outz
    # Index of the first sample we can't output yet:
    # TODO: Implementation that doesn't prepare a mixin.
    outz = minbleps.getmixin(naivex + blocksize, naiverate, outrate, 1, mixinmaster)[0]
    # Make space for all samples we can output plus overflow:
    outbuf = outmaster.ensureandcrop(outz - out0 + overflowsize)
    # Paste in the carry followed by the carried dc level:
    outbuf.buf[:len(carrybuf)] = carrybuf.buf
    outbuf.buf[len(carrybuf):] = dc
    for naivey in diffbuf.nonzeros():
      amp = diffbuf.buf[naivey]
      outi, mixin = minbleps.getmixin(naivex + naivey, naiverate, outrate, amp, mixinmaster)
      outj = outi + len(mixin.buf)
      outbuf.buf[outi - out0:outj - out0] += mixin.buf[:outj - outi]
      outbuf.buf[outj - out0:] += amp
    outbuf.buf[:outz - out0].tofile(sox.stdin)
    carrybuf.buf[:] = outbuf.buf[outz - out0:]
    naivex += blocksize
    dc = block.buf[-1]
    del diffbuf, outbuf # XXX: Why?
  sox.stdin.close()
  sys.exit(sox.wait())

if __name__ == '__main__':
  main()
