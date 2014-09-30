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

from __future__ import division
from pym2149.initlogging import logging
from pym2149.jackclient import JackClient
from pym2149.nod import Block
from config import getprocessconfig
import pypm, sys

log = logging.getLogger(__name__)

class Midi:

  def __init__(self):
    pypm.Initialize()

  def selectdevice(self):
    for i in xrange(pypm.CountDevices()):
      info = pypm.GetDeviceInfo(i)
      if info[2]: # It's an input device.
        print >> sys.stderr, "%2d) %s" % (i, info[1])
    print >> sys.stderr, 'Index? ',
    return Device(int(raw_input())) # Apparently int ignores whitespace.

  def dispose(self):
    pypm.Terminate()

class Device:

  def __init__(self, index):
    self.input = pypm.Input(index)

  def iterevents(self):
    while self.input.Poll():
      yield self.input.Read(1)

def main():
  config = getprocessconfig()
  midi = Midi()
  device = midi.selectdevice()
  jackclient = JackClient(config)
  chip, stream = jackclient.newchipandstream(None)
  try:
    minbleps = stream.wavs[0].minbleps
    naivex = 0
    while True:
      for event in device.iterevents():
        print event
      # Make min amount of chip data to get one JACK block:
      naiven = minbleps.getminnaiven(naivex, stream.size)
      stream.call(Block(naiven))
      naivex = (naivex + naiven) % chip.clock
  finally:
    stream.close()
  jackclient.dispose()
  midi.dispose()

if '__main__' == __name__:
  main()
