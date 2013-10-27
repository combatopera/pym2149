#!/usr/bin/env python

import logging
from pym2149.dosound import dosound
from pym2149.ym2149 import stclock
from pym2149.out import WavWriter
from pym2149.util import initlogging
from pym2149.mix import Mixer
from cli import Config

log = logging.getLogger(__name__)

def main():
  initlogging()
  config = Config()
  inpath, outpath = config.args
  f = open(inpath, 'rb')
  try:
    log.debug("Total ticks: %s", (ord(f.read(1)) << 8) | ord(f.read(1)))
    bytecode = [ord(c) for c in f.read()]
  finally:
    f.close()
  chip, session = config.createchipandsession(stclock)
  stream = WavWriter(session.clock, Mixer(*chip.dacs), outpath)
  try:
    dosound(bytecode, chip, session, stream)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
