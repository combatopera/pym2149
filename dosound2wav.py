#!/usr/bin/env python

from __future__ import division
from pym2149.initlogging import logging
from pym2149.dosound import dosound
from pym2149.ym2149 import stclock
from pym2149.out import WavWriter
from pym2149.util import Session
from pym2149.mix import IdealMixer
from budgie import readbytecode
from cli import Config

log = logging.getLogger(__name__)

extraseconds = 3

def main():
  config = Config()
  inpath, label, outpath = config.args
  f = open(inpath)
  try:
    bytecode = readbytecode(f, label)
  finally:
    f.close()
  chip = config.createchip(stclock)
  stream = WavWriter(chip.clock, IdealMixer(chip), outpath)
  try:
    session = Session(chip.clock)
    dosound(bytecode, chip, session, stream)
    log.info("Streaming %.3f extra seconds.", extraseconds)
    for b in session.blocks(1 / extraseconds):
      stream.call(b)
    stream.flush()
  finally:
    stream.close()

if '__main__' == __name__:
  main()
