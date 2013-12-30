#!/usr/bin/env python

from pym2149.initlogging import logging
from pym2149.out import WavWriter
from pym2149.util import Session
from pym2149.ymformat import ymopen
from pym2149.mix import Mixer
from cli import Config

log = logging.getLogger(__name__)

def main():
  config = Config()
  inpath, outpath = config.args
  f = ymopen(inpath, config)
  try:
    for info in f.info:
      log.info(info)
    chip = config.createchip(f.clock)
    stream = WavWriter(chip.clock, Mixer(chip), outpath)
    try:
      session = Session(chip.clock)
      for frame in f:
        chip.update(frame)
        for b in session.blocks(f.framefreq):
          stream.call(b)
      stream.flush()
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
