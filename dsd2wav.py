#!/usr/bin/env python

import sys, logging
from pym2149.dosound import dosound
from pym2149.ym2149 import YM2149, stclock as clock
from pym2149.out import WavWriter
from pym2149.util import Session, initlogging
from pym2149.mix import Mixer

log = logging.getLogger(__name__)

def main():
  initlogging()
  inpath, outpath = sys.argv[1:]
  f = open(inpath, 'rb')
  try:
    log.debug("Total ticks: %s", (ord(f.read(1)) << 8) | ord(f.read(1)))
    bytecode = [ord(c) for c in f.read()]
  finally:
    f.close()
  chip = YM2149()
  stream = WavWriter(clock, Mixer(*chip.dacs), outpath)
  try:
    dosound(bytecode, chip, Session(clock), stream)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
