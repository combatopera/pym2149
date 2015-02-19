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
from fractions import Fraction
from pym2149.config import getprocessconfig
from pym2149.di import DI
from pym2149.timer import Timer, SimpleTimer
from pym2149.out import configure
from pym2149.boot import createdi
from pym2149.iface import Chip, Stream
from pym2149.util import singleton
from ymplayer import ChipTimer
import os, subprocess, time

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.

@singleton
class orc(dict):

  def add(self, cls, key = None):
    if key is None:
      key = cls.__name__[0]
    if key in self:
      raise Exception("Key already in use: %s" % key)
    self[key] = cls
    return cls

class Updater:

  def __init__(self, onnote, chip, chan, frameindex):
    self.onnote = onnote
    self.chip = chip
    self.chan = chan
    self.frameindex = frameindex

  def update(self, frameindex):
    self.onnote.update(self.chip, self.chan, frameindex - self.frameindex)

@singleton
class voidupdater:

  def update(self, frameindex):
    pass

def main2(framesfactory, config):
    di = createdi(config)
    configure(di)
    chip = di(Chip)
    di.start()
    try:
      di.add(ChipTimer)
      timer = di(Timer)
      stream = di(Stream)
      chanupdaters = [voidupdater] * config.chipchannels
      for chan in xrange(1, config.chipchannels):
        chip.toneflags[chan].value = False
        chip.noiseflags[chan].value = False
        chip.fixedlevels[chan].value = 13 # Neutral DC.
      frames = framesfactory(chip)
      for frameindex, action in enumerate(frames):
        chan = 0
        onnoteornone = action.onnoteornone(chip, chan)
        if onnoteornone is not None:
          chanupdaters[chan] = Updater(onnoteornone, chip, chan, frameindex)
        for updater in chanupdaters:
          updater.update(frameindex)
        for b in timer.blocksforperiod(refreshrate):
          stream.call(b)
      stream.flush()
      return frames
    finally:
      di.stop()

class Boring:

  def __init__(self, orc):
    pass

  def update(self, chip, chan, frame):
    pass

@orc.add
class tone(Boring):

  def __init__(self, period):
    self.period = period

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = False
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.period

class Tone(tone):

  def __init__(self, nomclock):
    tone.__init__(self, Freq(self.freq).toneperiod(nomclock))

class Noise(Boring):

  def __init__(self, nomclock):
    self.period = Freq(self.freq).noiseperiod(nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = False
    chip.noiseflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.noiseperiod.value = self.period

class Both(Boring):

  def __init__(self, nomclock):
    self.tperiod = Freq(self.tfreq).toneperiod(nomclock)
    self.nperiod = Freq(self.nfreq).noiseperiod(nomclock)

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = True
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.tperiod
    chip.noiseperiod.value = self.nperiod

@orc.add
class Env(Boring):

  def __init__(self, freq, shape):
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

  def __init__(self, tfreq, nfreq, efreq, shape):
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

  def __init__(self, tfreq, tsfreq):
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

  def __init__(self, config):
    self.targetpath = os.path.join(os.path.dirname(__file__), 'target')
    if not os.path.exists(self.targetpath):
      os.mkdir(self.targetpath)
    self.config = config

  def dump(self, chanfactory, name):
    path = os.path.join(self.targetpath, name)
    log.debug(path)
    start = time.time()
    config = self.config.fork()
    config.outpath = path + '.wav'
    chan = main2(chanfactory, config)
    log.info("Render of %.3f seconds took %.3f seconds.", len(chan) / refreshrate, time.time() - start)
    subprocess.check_call(['sox', path + '.wav', '-n', 'spectrogram', '-o', path + '.png'])

class NoteAction:

  def __init__(self, note):
    self.note = note

  def onnoteornone(self, chip, chan):
    # The note needn't know all the chip's features, so turn them off first:
    chip.flagsoff(chan)
    self.note.noteon(chip, chan)
    return self.note

@singleton
class sustainaction:

  def onnoteornone(self, chip, chan):
    pass

def getorlast(v, i):
  try:
    return v[i]
  except IndexError:
    return v[-1]

def play(beatsperbar, beats, *args):
  def framesfactory(chip):
    timer = SimpleTimer(refreshrate)
    frames = []
    paramindex = 0
    for char in beats:
      if '.' == char:
        action = sustainaction
      else:
        nargs = [getorlast(v, paramindex) for v in args]
        program = orc[char]
        note = program(*nargs)
        action = NoteAction(note)
        paramindex += 1
      frames.append(action)
      b, = timer.blocksforperiod(beatsperbar)
      for _ in xrange(b.framecount - 1):
        frames.append(sustainaction)
    return frames
  return framesfactory

class Play:

  def __init__(self, config):
    self.nomclock = config.nominalclock

  def __call__(self, beatsperbar, beats):
    def framesfactory(chip):
      timer = SimpleTimer(refreshrate)
      frames = []
      for program in beats:
        if not program:
          action = sustainaction
        else:
          note = program(self.nomclock)
          action = NoteAction(note)
        frames.append(action)
        b, = timer.blocksforperiod(beatsperbar)
        for _ in xrange(b.framecount - 1):
          frames.append(sustainaction)
      return frames
    return framesfactory

def main():
  config = getprocessconfig()
  config.di = DI()
  orc.nomclock = config.nominalclock # FIXME: Too eager.
  play2 = Play(config)
  target = Target(config)
  class T250(Tone): freq = 250
  target.dump(play2(2, [T250, 0, 0]), 'tone250')
  class T1k(Tone): freq = 1000
  target.dump(play2(2, [T1k, 0, 0]), 'tone1k')
  class T1k5(Tone): freq = 1500
  target.dump(play2(2, [T1k5, 0, 0]), 'tone1k5')
  class N5k(Noise): freq = 5000
  target.dump(play2(2, [N5k, 0, 0]), 'noise5k')
  class N125k(Noise): freq = 125000
  target.dump(play2(2, [N125k, 0, 0]), 'noise125k')
  class T1kN5k(Both): tfreq, nfreq = 1000, 5000
  target.dump(play2(2, [T1kN5k, 0, 0]), 'tone1k+noise5k')
  class T1N5k(Both): tfreq, nfreq = config.nominalclock // 16, 5000
  target.dump(play2(2, [T1N5k, 0, 0]), 'noise5k+tone1')
  target.dump(play(2, 'E..', [600], [0x08]), 'saw600')
  target.dump(play(2, 'E..', [600], [0x10]), 'sin600')
  target.dump(play(2, 'E..', [650], [0x0a]), 'tri650')
  target.dump(play(2, 'A..', [1000], [5000], [1], [0x0e]), 'tone1k+noise5k+tri1')
  class T2k(Tone): freq = 2000
  class T3k(Tone): freq = 3000
  class T4k(Tone): freq = 4000
  target.dump(play2(4, [T1k, T2k, T3k, T4k]), 'tone1k,2k,3k,4k')
  target.dump(play(2, 'P..', [501], [501]), 'pwm501')
  target.dump(play(2, 'P..', [250], [251]), 'pwm250') # Observe timer detune.
  target.dump(play(8, 't'*8, range(1, 9)), 'tone1-8')

if '__main__' == __name__:
  main()
