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
from pym2149.pitch import Freq
from music import Orc, Main, clock as nomclock
import os, subprocess

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.
orc = Orc(refreshrate) # A bar is exactly 1 second long.

class Boring:

  def update(self, chip, chan, frame):
    pass

@orc.add
class Silence(Boring):

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = False
    chip.fixedlevels[chan].value = 13

@orc.add
class Tone(Boring):

  def __init__(self, freq):
    self.period = Freq(freq).toneperiod(nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = False
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.period

@orc.add
class Noise(Boring):

  def __init__(self, freq):
    self.period = Freq(freq).noiseperiod(nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.noiseperiod.value = self.period

@orc.add
class Both(Boring):

  def __init__(self, tfreq, nfreq):
    self.tperiod = Freq(tfreq).toneperiod(nomclock)
    self.nperiod = Freq(nfreq).noiseperiod(nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.tperiod
    chip.noiseperiod.value = self.nperiod

@orc.add
class Env(Boring):

  def __init__(self, freq, shape):
    self.period = Freq(freq).envperiod(nomclock, shape)
    self.shape = shape

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = False
    chip.levelmodes[chan].value = 1
    chip.envperiod.value = self.period
    chip.envshape.value = self.shape

@orc.add
class All(Boring):

  def __init__(self, tfreq, nfreq, efreq, shape):
    self.tperiod = Freq(tfreq).toneperiod(nomclock)
    self.nperiod = Freq(nfreq).noiseperiod(nomclock)
    self.eperiod = Freq(efreq).envperiod(nomclock, shape)
    self.shape = shape

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = True
    chip.levelmodes[chan].value = 1
    chip.toneperiods[chan].value = self.tperiod
    chip.noiseperiod.value = self.nperiod
    chip.envperiod.value = self.eperiod
    chip.envshape.value = self.shape

class Target:

  with orc as play: dc0 = play(1, 'S')
  main = Main(refreshrate)

  def __init__(self):
    self.targetpath = os.path.join(os.path.dirname(__file__), 'target')
    if not os.path.exists(self.targetpath):
      os.mkdir(self.targetpath)

  def dump(self, chan, name):
    path = os.path.join(self.targetpath, name)
    log.debug(path)
    self.main(zip(chan, self.dc0, self.dc0), [path + '.wav'])
    subprocess.check_call(['sox', path + '.wav', '-n', 'spectrogram', '-o', path + '.png'])

def main():
  target = Target()
  with orc as play: target.dump(play(1, 'T', [250]), '250tone')
  with orc as play: target.dump(play(1, 'T', [1000]), '1ktone')
  with orc as play: target.dump(play(1, 'T', [1500]), '1k5tone')
  with orc as play: target.dump(play(1, 'N', [5000]), '5knoise')
  with orc as play: target.dump(play(1, 'B', [1000], [5000]), '1ktone5knoise')
  with orc as play: target.dump(play(1, 'E', [600], [0x08]), '600saw')
  with orc as play: target.dump(play(1, 'E', [600], [0x10]), '600sin')
  with orc as play: target.dump(play(1, 'E', [650], [0x0a]), '650tri')
  with orc as play: target.dump(play(1, 'A', [1000], [5000], [1], [0x0e]), '1tri1ktone5knoise')

if '__main__' == __name__:
  main()
