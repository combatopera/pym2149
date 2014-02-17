#!/usr/bin/env python

from __future__ import division
import numpy as np, random
from pym2149.buf import Buf
from pym2149.nod import Node, Block
from pym2149.out import WavWriter

class Chip(Node):

  naiverate = 2000000

  def __init__(self):
    Node.__init__(self)
    tonefreq = 1500
    toneamp = .25 * 2 ** 15
    self.naivesize = self.naiverate * 60 # One minute of data.
    toneoscscale = 16 # A property of the chip.
    periodreg = int(round(self.naiverate / (toneoscscale * tonefreq)))
    period = toneoscscale * periodreg # Even.
    self.naivebuf = Buf(np.empty(self.naivesize))
    x = 0
    while x < self.naivesize:
      self.naivebuf.fillpart(x, x + period // 2, toneamp)
      self.naivebuf.fillpart(x + period // 2, x + period, -toneamp)
      x += period
    self.cursor = 0

  def callimpl(self):
    self.cursor += self.block.framecount
    return Buf(self.naivebuf.buf[self.cursor - self.block.framecount:self.cursor])

def main():
  chip = Chip()
  stream = WavWriter(chip.naiverate, chip, 'minbleppoc.wav')
  while chip.cursor < chip.naivesize:
    stream.call(Block(random.randint(1, 30000)))
  stream.close()

if __name__ == '__main__':
  main()
