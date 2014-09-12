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
from music import Orc, Main
from fractions import Fraction
from config import getprocessconfig
import os, subprocess, time, sys

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.
orc = Orc(refreshrate) # A bar is exactly 1 second long.

class Boring:

  def __init__(self, orc):
    pass

  def update(self, chip, chan, frame):
    pass

@orc.add
class silence(Boring):

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = False
    chip.fixedlevels[chan].value = 13

@orc.add
class tone(Boring):

  def __init__(self, orc, period):
    self.period = period

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = False
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.period

@orc.add
class Tone(tone):

  def __init__(self, orc, freq):
    tone.__init__(self, orc, Freq(freq).toneperiod(orc.nomclock))

@orc.add
class Noise(Boring):

  def __init__(self, orc, freq):
    self.period = Freq(freq).noiseperiod(orc.nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.noiseperiod.value = self.period

@orc.add
class Both(Boring):

  def __init__(self, orc, tfreq, nfreq):
    self.tperiod = Freq(tfreq).toneperiod(orc.nomclock)
    self.nperiod = Freq(nfreq).noiseperiod(orc.nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.tperiod
    chip.noiseperiod.value = self.nperiod

@orc.add
class Env(Boring):

  def __init__(self, orc, freq, shape):
    self.period = Freq(freq).envperiod(orc.nomclock, shape)
    self.shape = shape

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = False
    chip.levelmodes[chan].value = 1
    chip.envperiod.value = self.period
    chip.envshape.value = self.shape

@orc.add
class All(Boring):

  def __init__(self, orc, tfreq, nfreq, efreq, shape):
    self.tperiod = Freq(tfreq).toneperiod(orc.nomclock)
    self.nperiod = Freq(nfreq).noiseperiod(orc.nomclock)
    self.eperiod = Freq(efreq).envperiod(orc.nomclock, shape)
    self.shape = shape

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = True
    chip.levelmodes[chan].value = 1
    chip.toneperiods[chan].value = self.tperiod
    chip.noiseperiod.value = self.nperiod
    chip.envperiod.value = self.eperiod
    chip.envshape.value = self.shape

@orc.add
class PWM(Boring):

  def __init__(self, orc, tfreq, tsfreq):
    self.tperiod = Freq(tfreq).toneperiod(orc.nomclock)
    self.tsfreq = Fraction(tsfreq)

  def noteon(self, chip, chan):
    chip.noiseflags[chan].value = False
    chip.toneflags[chan].value = True
    chip.tsflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.tperiod
    chip.tsfreqs[chan].value = self.tsfreq

class Target:

  with orc as play: dc0 = play(1, 's'*10)
  main = Main(refreshrate)

  def __init__(self):
    self.targetpath = os.path.join(os.path.dirname(__file__), 'target')
    if not os.path.exists(self.targetpath):
      os.mkdir(self.targetpath)

  def dump(self, chan, name):
    path = os.path.join(self.targetpath, name)
    log.debug(path)
    frames = zip(chan, self.dc0, self.dc0)
    start = time.time()
    self.main(frames, sys.argv[1:] + [path + '.wav'])
    log.info("Render of %.3f seconds took %.3f seconds.", len(frames) / refreshrate, time.time() - start)
    subprocess.check_call(['sox', path + '.wav', '-n', 'spectrogram', '-o', path + '.png'])

def main():
  orc.nomclock = getprocessconfig().getnominalclock()
  target = Target()
  with orc as play: target.dump(play(2, 'T..', [250]), 'tone250')
  with orc as play: target.dump(play(2, 'T..', [1000]), 'tone1k')
  with orc as play: target.dump(play(2, 'T..', [1500]), 'tone1k5')
  with orc as play: target.dump(play(2, 'N..', [5000]), 'noise5k')
  with orc as play: target.dump(play(2, 'N..', [125000]), 'noise125k')
  with orc as play: target.dump(play(2, 'B..', [1000], [5000]), 'tone1k+noise5k')
  with orc as play: target.dump(play(2, 'B..', [orc.nomclock // 16], [5000]), 'noise5k+tone1')
  with orc as play: target.dump(play(2, 'E..', [600], [0x08]), 'saw600')
  with orc as play: target.dump(play(2, 'E..', [600], [0x10]), 'sin600')
  with orc as play: target.dump(play(2, 'E..', [650], [0x0a]), 'tri650')
  with orc as play: target.dump(play(2, 'A..', [1000], [5000], [1], [0x0e]), 'tone1k+noise5k+tri1')
  with orc as play: target.dump(play(4, 'TTTT', [1000,2000,3000,4000]), 'tone1k,2k,3k,4k')
  with orc as play: target.dump(play(2, 'P..', [501], [501]), 'pwm501')
  with orc as play: target.dump(play(2, 'P..', [250], [251]), 'pwm250') # Observe timer detune.
  with orc as play: target.dump(play(8, 't'*8, range(1, 9)), 'tone1-8')

if '__main__' == __name__:
  main()
