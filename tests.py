#!/usr/bin/env python

from __future__ import division
from pym2149.out import WavWriter
from pym2149.util import blocks
from pym2149.ym2149 import YM2149
import sys, os

clock = 2000000 # Atari ST.
outfreq = 44100
refreshrate = 60 # Deliberately not a divisor of the clock.
seconds = 8 / 7 # Deliberately a non-nice number.
tonenote = 1000 # First peak should have this frequency.
noisenote = 5000 # First trough should have this frequency, authentic by qnoispec.
sawnote = 600 # First peak should have this frequency.
trinote = 1300 # First peak should have half this frequency.
slowtrinote = 2

def main():
  x = YM2149(1)
  for i in xrange(x.channels):
    x.toneflags[i].value = False
    x.noiseflags[i].value = False
  x.toneperiods[0].value = int(round(clock / (16 * tonenote)))
  x.noiseperiod.value = int(round(clock / (16 * noisenote)))
  x.fixedlevels[0].value = 15
  def dump(path):
    path = os.path.join('target', path)
    print >> sys.stderr, path
    w = WavWriter(1, clock, x, outfreq, path)
    for block in blocks(clock, refreshrate, seconds):
      w(block)
    w.close()
  x.toneflags[0].value = True
  dump('1ktone.wav')
  x.toneflags[0].value = False
  x.noiseflags[0].value = True
  dump('5knoise.wav')
  x.toneflags[0].value = True
  dump('1ktone5knoise.wav')
  x.toneflags[0].value = False
  x.noiseflags[0].value = False
  x.levelmodes[0].value = 1 # Envelope on.
  x.envperiod.value = int(round(clock / (256 * sawnote)))
  x.envshape.value = 0x08
  dump('600saw.wav')
  x.envperiod.value = int(round(clock / (256 * trinote)))
  x.envshape.value = 0x0a
  dump('650tri.wav')
  x.envperiod.value = int(round(clock / (256 * slowtrinote)))
  x.toneflags[0].value = True
  x.noiseflags[0].value = True
  dump('1tri1ktone5knoise.wav')

if '__main__' == __name__:
  main()
