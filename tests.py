#!/usr/bin/env python

from __future__ import division
from psg.out import WavWriter
from psg.nod import Block
from ym2149 import YM2149
import sys

clock = 2000000
outfreq = 44100
refreshrate = 60
seconds = .9
tonenote = 1000
noisenote = 5000

def blocks():
  framecount = int(round(seconds * clock))
  frameindex = 0
  carry = 0
  while frameindex < framecount:
    blocksize = min(framecount - frameindex, clock // refreshrate)
    carry += clock % refreshrate
    while carry >= refreshrate:
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

if '__main__' == __name__:
  main()
