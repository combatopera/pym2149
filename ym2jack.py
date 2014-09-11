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
from pym2149.timer import Timer
from pym2149.ymformat import ymopen
from pym2149.nod import Node, BufNode
from cli import getprocessconfig
from roll import Roll
import jack, numpy as np

log = logging.getLogger(__name__)

clientname = 'pym2149'
# XXX: Can we detect how many system channels there are?
systemchannels = tuple("system:playback_%s" % (1 + i) for i in xrange(2))

class JackWriter(Node):

  def __init__(self, wavs):
    Node.__init__(self)
    jack.register_port('in_1', jack.IsInput) # Apparently necessary.
    for i in xrange(len(wavs)):
      jack.register_port("out_%s" % (1 + i), jack.IsOutput)
    jack.activate()
    # Connect all system channels, cycling over our streams if necessary:
    for i, systemchannel in enumerate(systemchannels):
      clientchannelindex = i % len(wavs)
      jack.connect("%s:out_%s" % (clientname, 1 + clientchannelindex), systemchannel)
    self.size = jack.get_buffer_size()
    self.jack = np.empty((len(wavs), self.size), dtype = BufNode.floatdtype)
    self.empty = np.empty((1, self.size), dtype = BufNode.floatdtype)
    self.cursor = 0
    self.wavs = wavs

  def callimpl(self):
    outbufs = [self.chain(wav) for wav in self.wavs]
    n = len(outbufs[0])
    i = 0
    while i < n:
      m = min(n - i, self.size - self.cursor)
      for c in xrange(len(self.wavs)):
        self.jack[c, self.cursor:self.cursor + m] = outbufs[c].buf[i:i + m]
      self.cursor += m
      i += m
      if self.cursor == self.size:
        try:
          jack.process(self.jack, self.empty)
        except (jack.InputSyncError, jack.OutputSyncError):
          log.warn('JACK error:', exc_info = True)
        self.cursor = 0

  def close(self):
    jack.deactivate()

def main():
  config = getprocessconfig()
  inpath, = config.args
  jack.attach(clientname)
  config.outrate = jack.get_sample_rate() # Override user setting if any.
  f = ymopen(inpath, config)
  try:
    for info in f.info:
      log.info(info)
    # For jack the available amplitude range is 2 ** 1:
    chip = config.createchip(nominalclock = f.clock, bits = 1)
    stream = JackWriter(config.createfloatstream(chip))
    try:
      timer = Timer(chip.clock) # TODO LATER: Support sync with jack block schedule.
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
  jack.detach()

if '__main__' == __name__:
  main()
