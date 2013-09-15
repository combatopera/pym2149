#!/usr/bin/env python

import sys, logging
from pym2149.out import WavWriter
from pym2149.util import blocks
from pym2149.ym2149 import YM2149
from ymformat import ymopen

log = logging.getLogger(__name__)

def main():
  logging.basicConfig(format = "[%(levelname)s] %(message)s", level = logging.INFO)
  inpath, outpath = sys.argv[1:]
  f = ymopen(inpath)
  try:
    for info in f.info:
      log.info(info)
    chip = YM2149()
    stream = WavWriter(1, f.clock, chip, 44100, outpath)
    try:
      bi = blocks(f.clock, f.framefreq)
      for frame in f:
        chip.update(frame)
        stream(bi.next())
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
