#!/usr/bin/env python

import sys, logging
from pym2149.out import WavWriter
from pym2149.util import Session, initlogging
from pym2149.ym2149 import YM2149
from ymformat import ymopen

log = logging.getLogger(__name__)

def main():
  initlogging()
  inpath, outpath = sys.argv[1:]
  f = ymopen(inpath)
  try:
    for info in f.info:
      log.info(info)
    chip = YM2149()
    stream = WavWriter(f.clock, chip, outpath)
    try:
      session = Session(f.clock)
      for frame in f:
        chip.update(frame)
        stream(session.block(f.framefreq))
      stream.flush()
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
