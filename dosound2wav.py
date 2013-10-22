#!/usr/bin/env python

from __future__ import division
import sys, logging
from pym2149.dosound import dosound
from pym2149.ym2149 import YM2149, stclock as clock
from pym2149.out import WavWriter
from pym2149.util import Session, initlogging
from budgie import readbytecode

log = logging.getLogger(__name__)

extraseconds = 3

def main():
  initlogging()
  inpath, label, outpath = sys.argv[1:]
  f = open(inpath)
  try:
    bytecode = readbytecode(f, label)
  finally:
    f.close()
  chip = YM2149()
  stream = WavWriter(clock, chip, outpath)
  try:
    session = Session(clock)
    dosound(bytecode, chip, session, stream)
    log.info("Streaming %.3f extra seconds.", extraseconds)
    for b in session.blocks(1 / extraseconds):
      stream(b)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
