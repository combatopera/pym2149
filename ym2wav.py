#!/usr/bin/env python

from __future__ import division
import sys, logging, getopt
from pym2149.out import WavWriter
from pym2149.util import Session, initlogging
from pym2149.ym2149 import YM2149, defaultscale
from pym2149.ymformat import ymopen
from pym2149.mix import Mixer

log = logging.getLogger(__name__)

def uniqueoption(options, keys, defaultval, xform):
  vals = [v for k, v in options if k in keys]
  if not vals:
    return defaultval
  v, = vals
  return xform(v)

def main():
  initlogging()
  options, args = getopt.getopt(sys.argv[1:], 's:', ['scale='])
  scale = uniqueoption(options, ('-s', '--scale'), defaultscale, int)
  inpath, outpath = args
  f = ymopen(inpath)
  try:
    for info in f.info:
      log.info(info)
    chip = YM2149(scale = scale)
    clock = f.clock * scale / 8 # Observe may be non-integer.
    if scale != defaultscale:
      log.debug("Clock adjusted to %.3f for non-standard scale.", clock)
    stream = WavWriter(clock, Mixer(*chip.dacs), outpath)
    try:
      session = Session(clock)
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
