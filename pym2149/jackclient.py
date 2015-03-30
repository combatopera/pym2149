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

from nod import Node, BufNode
from const import clientname
from iface import AmpScale
from out import FloatStream
from iface import Stream, JackConnection
from di import types
import jack, numpy as np, logging

log = logging.getLogger(__name__)

class JackClient(JackConnection):

  @types()
  def __init__(self): pass

  def start(self):
    jack.attach(clientname)
    self.outputrate = jack.get_sample_rate()

  def get_buffer_size(self):
    return jack.get_buffer_size()

  def activate(self):
    jack.activate()

  def deactivate(self):
    jack.deactivate()

  def stop(self):
    jack.detach()

class JackStream(object, Node, Stream):

  __metaclass__ = AmpScale
  # For jack the available amplitude range is 2 ** 1:
  log2maxpeaktopeak = 1
  # XXX: Can we detect how many system channels there are?
  systemchannels = tuple("system:playback_%s" % (1 + i) for i in xrange(2))

  @types(FloatStream, JackClient)
  def __init__(self, wavs, client):
    Node.__init__(self)
    jack.register_port('in_1', jack.IsInput) # Apparently necessary.
    for i in xrange(len(wavs)):
      jack.register_port("out_%s" % (1 + i), jack.IsOutput)
    self.bufferx = 0
    self.wavs = wavs
    self.client = client

  def start(self):
    self.buffersize = self.client.get_buffer_size()
    self.client.activate()
    # Connect all system channels, cycling over our streams if necessary:
    for i, systemchannel in enumerate(self.systemchannels):
      clientchannelindex = i % len(self.wavs)
      jack.connect("%s:out_%s" % (clientname, 1 + clientchannelindex), systemchannel)
    self.data = np.empty((len(self.wavs), self.buffersize), dtype = BufNode.floatdtype)
    self.empty = np.empty((1, self.buffersize), dtype = BufNode.floatdtype)

  def callimpl(self):
    outbufs = [self.chain(wav) for wav in self.wavs]
    n = len(outbufs[0])
    i = 0
    while i < n:
      m = min(n - i, self.buffersize - self.bufferx)
      for c in xrange(len(self.wavs)):
        outbufs[c].partcopyintonp(i, i + m, self.data[c, self.bufferx:self.bufferx + m])
      self.bufferx += m
      i += m
      if self.bufferx == self.buffersize:
        try:
          jack.process(self.data, self.empty)
        except (jack.InputSyncError, jack.OutputSyncError):
          log.warn('JACK error:', exc_info = True)
        self.bufferx = 0

  def flush(self):
    pass # Nothing to be done.

  def stop(self):
    self.client.deactivate()

def configure(di):
    di.add(JackStream)
