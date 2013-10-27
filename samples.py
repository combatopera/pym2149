#!/usr/bin/env python

from __future__ import division
from pym2149.out import WavWriter
from pym2149.util import Session, initlogging
from pym2149.ym2149 import YM2149, stclock as clock
from pym2149.mix import Mixer
import os, logging

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.
seconds = 8 / 7 # Deliberately a non-nice number.
tonenote = 1000 # First peak should have this frequency.
noisenote = 5000 # First trough should have this frequency, authentic by qnoispec.
sawnote = 600 # First peak should have this frequency.
trinote = 1300 # First peak should have half this frequency.
slowtrinote = 2 # Frequency and actual period are both 1.

def main():
  initlogging()
  chip = YM2149(1) # Stretch 1 channel to full range.
  for c in xrange(chip.channels):
    chip.toneflags[c].value = False
    chip.noiseflags[c].value = False
  chip.toneperiods[0].value = int(round(clock / (16 * tonenote)))
  chip.noiseperiod.value = int(round(clock / (16 * noisenote)))
  chip.fixedlevels[0].value = 15
  def dump(path):
    path = os.path.join('target', path)
    log.debug(path)
    stream = WavWriter(clock, Mixer(*chip.dacs), path)
    try:
      session = Session(clock)
      # Closest number of frames to desired number of seconds:
      for i in xrange(int(round(seconds * refreshrate))):
        for b in session.blocks(refreshrate):
          stream(b)
      stream.flush()
    finally:
      stream.close()
  chip.toneflags[0].value = True
  dump('1ktone.wav')
  chip.toneflags[0].value = False
  chip.noiseflags[0].value = True
  dump('5knoise.wav')
  chip.toneflags[0].value = True
  dump('1ktone5knoise.wav')
  chip.toneflags[0].value = False
  chip.noiseflags[0].value = False
  chip.levelmodes[0].value = 1 # Envelope on.
  chip.envperiod.value = int(round(clock / (256 * sawnote)))
  chip.envshape.value = 0x08
  dump('600saw.wav')
  chip.envperiod.value = int(round(clock / (256 * trinote)))
  chip.envshape.value = 0x0a
  dump('650tri.wav')
  chip.envperiod.value = int(round(clock / (256 * slowtrinote)))
  chip.toneflags[0].value = True
  chip.noiseflags[0].value = True
  dump('1tri1ktone5knoise.wav')

if '__main__' == __name__:
  main()
