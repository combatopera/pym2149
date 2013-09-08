#!/usr/bin/env python

from __future__ import division
from pym2149.out import WavWriter
from pym2149.nod import Block
from pym2149.ym2149 import YM2149
import sys

clock = 2000000 # Atari ST.
outfreq = 44100
refreshrate = 60 # Deliberately not a divisor of the clock.
seconds = 8 / 7 # Deliberately a non-nice number.
tonenote = 1000 # First peak should have this frequency.
noisenote = 5000 # First trough should have this frequency. XXX: Is that authentic?
sawnote = 600 # First peak should have this frequency.
trinote = 1300 # First peak should have half this frequency.

def blocks():
  framecount = int(round(seconds * clock))
  frameindex = 0
  carry = 0
  while frameindex < framecount:
    blocksize = min(framecount - frameindex, clock // refreshrate)
    carry += clock % refreshrate
    while carry >= refreshrate: # Probably at most once.
      blocksize += 1
      carry -= refreshrate
    yield Block(blocksize)
    frameindex += blocksize

def main():
  x = YM2149()
  for i in xrange(x.channels):
    x.toneflags[i].value = 1
    x.noiseflags[i].value = 1
  x.toneperiods[0].value = int(round(clock / (16 * tonenote)))
  x.noiseperiod.value = int(round(clock / (16 * noisenote)))
  x.fixedlevels[0].value = 15
  def dump(path):
    print >> sys.stderr, path
    w = WavWriter(1, clock, x, outfreq, path)
    for block in blocks():
      w(block)
    w.close()
  x.toneflags[0].value = 0
  dump('1ktone.wav')
  x.toneflags[0].value = 1
  x.noiseflags[0].value = 0
  dump('5knoise.wav')
  x.toneflags[0].value = 0
  dump('1ktone5knoise.wav')
  x.noiseflags[0].value = 1 # Noise off.
  x.levelmodes[0].value = 1 # Envelope on.
  x.toneperiods[0].value = (1 << 12) - 1 # Max period.
  x.envperiod.value = int(round(clock / (256 * sawnote)))
  x.envshape.value = 0x08
  dump('600saw.wav')
  x.envperiod.value = int(round(clock / (256 * trinote)))
  x.envshape.value = 0x0a
  dump('650tri.wav')

if '__main__' == __name__:
  main()
