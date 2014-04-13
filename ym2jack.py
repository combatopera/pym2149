#!/usr/bin/env python

# Copyright 2014 Andrzej Cichocki

# This file is part of pym2149.
#
# pym2149 is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pym2149 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pym2149.  If not, see <http://www.gnu.org/licenses/>.

from pym2149.initlogging import logging
from pym2149.util import Timer
from pym2149.ymformat import ymopen
from pym2149.nod import Node, BufNode
from pym2149.dac import Dac
from cli import Config
from ym2wav import Roll
import jack, numpy as np

log = logging.getLogger(__name__)

class JackWriter(Node):

  def __init__(self, wav):
    Node.__init__(self)
    clientname = 'pym2149'
    jack.attach(clientname)
    jack.register_port('in_1', jack.IsInput)
    for i in xrange(wav.channels):
      jack.register_port("out_%s" % (1 + i), jack.IsOutput)
    jack.activate()
    for i in xrange(wav.channels):
      jack.connect("%s:out_%s" % (clientname, 1 + i), "alsa_pcm:playback_%s" % (1 + i))
    size = jack.get_buffer_size()
    self.size = wav.channels * size
    self.jack = np.empty(self.size, dtype = BufNode.floatdtype)
    self.jack2 = self.jack.reshape((wav.channels, size), order = 'F')
    self.empty = np.empty((1, size), dtype = BufNode.floatdtype)
    self.cursor = 0
    self.wav = wav

  def callimpl(self):
    outbuf = self.chain(self.wav)
    n = len(outbuf) # Samples i.e. channels times frames.
    i = 0
    while i < n:
      m = min(n - i, self.size - self.cursor)
      self.jack[self.cursor:self.cursor + m] = outbuf.buf[i:i + m]
      self.cursor += m
      i += m
      if self.cursor == self.size:
        self.jack2 /= Dac.amprange
        jack.process(self.jack2, self.empty)
        self.cursor = 0

  def close(self):
    jack.deactivate()
    jack.detach()

def main():
  config = Config()
  inpath, = config.args
  f = ymopen(inpath, config)
  try:
    for info in f.info:
      log.info(info)
    chip = config.createchip(nominalclock = f.clock)
    stream = JackWriter(config.createfloatstream(chip))
    try:
      timer = Timer(chip.clock)
      roll = Roll(config.getheight(f.framefreq), chip, f.clock)
      for frame in f:
        frame(chip)
        roll.update()
        for b in timer.blocks(f.framefreq):
          stream.call(b)
    finally:
      stream.close()
  finally:
    f.close()

if '__main__' == __name__:
  main()
