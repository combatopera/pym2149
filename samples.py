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
from pym2149.out import WavWriter
from pym2149.util import Session
from pym2149.ym2149 import stclock as nomclock
from pym2149.mix import IdealMixer
from cli import Config
import os, subprocess

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.
seconds = 8 / 7 # Deliberately a non-nice number.
tonenote = 1000 # First peak should have this frequency.
noisenote = 5000 # First trough should have this frequency, authentic by qnoispec.
sawnote = 600 # First peak should have this frequency.
trinote = 1300 # First peak should have half this frequency.
slowtrinote = 2 # Frequency and actual period are both 1.

class Samples:

  def __init__(self):
    self.config = Config()
    self.targetpath = os.path.join(os.path.dirname(__file__), 'target')
    if not os.path.exists(self.targetpath):
      os.mkdir(self.targetpath)

  def dump(self, sample):
    chip = self.config.createchip(nomclock)
    for c in xrange(chip.channels):
      chip.toneflags[c].value = False
      chip.noiseflags[c].value = False
    chip.toneperiods[0].value = int(round(nomclock / (16 * tonenote)))
    chip.noiseperiod.value = int(round(nomclock / (16 * noisenote)))
    chip.fixedlevels[0].value = 15
    sample(chip)
    name = sample.__name__
    if name.startswith('_'):
      name = name[1:]
    path = os.path.join(self.targetpath, name)
    log.debug(path)
    stream = WavWriter(chip.clock, IdealMixer(chip), path + '.wav')
    try:
      session = Session(chip.clock)
      # Closest number of frames to desired number of seconds:
      for i in xrange(int(round(seconds * refreshrate))):
        for b in session.blocks(refreshrate):
          stream.call(b)
      stream.flush()
    finally:
      stream.close()
    subprocess.check_call(['sox', path + '.wav', '-n', 'spectrogram', '-o', path + '.png'])

def main():
  samples = Samples()
  def _1ktone(chip):
    chip.toneflags[0].value = True
  samples.dump(_1ktone)
  def _5knoise(chip):
    chip.noiseflags[0].value = True
  samples.dump(_5knoise)
  def _1ktone5knoise(chip):
    chip.noiseflags[0].value = True
    chip.toneflags[0].value = True
  samples.dump(_1ktone5knoise)
  def _600saw(chip):
    chip.levelmodes[0].value = 1 # Envelope on.
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x08
  samples.dump(_600saw)
  def _600sin(chip):
    chip.levelmodes[0].value = 1 # Envelope on.
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x08
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x10
  samples.dump(_600sin)
  def _650tri(chip):
    chip.levelmodes[0].value = 1 # Envelope on.
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x08
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x10
    chip.envperiod.value = int(round(nomclock / (256 * trinote)))
    chip.envshape.value = 0x0a
  samples.dump(_650tri)
  def _1tri1ktone5knoise(chip):
    chip.levelmodes[0].value = 1 # Envelope on.
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x08
    chip.envperiod.value = int(round(nomclock / (256 * sawnote)))
    chip.envshape.value = 0x10
    chip.envperiod.value = int(round(nomclock / (256 * trinote)))
    chip.envshape.value = 0x0a
    chip.envperiod.value = int(round(nomclock / (256 * slowtrinote)))
    chip.toneflags[0].value = True
    chip.noiseflags[0].value = True
  samples.dump(_1tri1ktone5knoise)

if '__main__' == __name__:
  main()
