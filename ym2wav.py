#!/usr/bin/env python

import sys
from pym2149.out import WavWriter
from pym2149.util import blocks
from pym2149.ym2149 import YM2149
from ymformat import YM6File

def main():
  inpath, outpath = sys.argv[1:]
  f = open(inpath, 'rb')
  try:
    f = YM6File(f)
    for info in f.info:
      print >> sys.stderr, info
    print >> sys.stderr, 'samplecount:', f.samplecount
    x = YM2149()
    y = WavWriter(1, f.clock, x, 44100, outpath)
    try:
      bi = blocks(f.clock, f.framefreq)
      for frame in f:
        x.update(frame)
        y(bi.next())
    finally:
      y.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
