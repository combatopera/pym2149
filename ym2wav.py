#!/usr/bin/env python

import sys, logging
from pym2149.out import WavWriter
from pym2149.util import Session, initlogging
from pym2149.ym2149 import YM2149
from pym2149.ymformat import ymopen
from pym2149.mix import Mixer

log = logging.getLogger(__name__)

def main():
  initlogging()
  inpath, outpath = sys.argv[1:]
  f = ymopen(inpath)
  try:
    for info in f.info:
      log.info(info)
    chip = YM2149()
    stream = WavWriter(f.clock, Mixer(*chip.dacs), outpath)
    try:
      session = Session(f.clock)
      for frame in f:
        chip.update(frame)
        for b in session.blocks(f.framefreq):
          stream(b)
      stream.flush()
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
