#!/usr/bin/env python

import sys
from pym2149.dosound import dosound
from pym2149.ym2149 import YM2149, stclock as clock
from pym2149.out import WavWriter
from pym2149.util import Session

def main():
  inpath, outpath = sys.argv[1:]
  f = open(inpath)
  try:
    f.read(2) # Skip total ticks.
    bytecode = [ord(c) for c in f.read()]
  finally:
    f.close()
  chip = YM2149()
  stream = WavWriter(clock, chip, outpath)
  try:
    dosound(bytecode, chip, Session(clock), stream)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
