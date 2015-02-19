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
from pym2149.program import Note
from ymplayer import ChipTimer
import os, subprocess, time

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.
activechan = 0

class Updater:

  def __init__(self, onnote, frameindex):
    self.onnote = onnote
    self.frameindex = frameindex

  def update(self, frameindex):
    self.onnote.noteonframe(frameindex - self.frameindex)

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
      for chan in xrange(config.chipchannels):
        if chan != activechan:
          chip.toneflags[chan].value = False
          chip.noiseflags[chan].value = False
          chip.fixedlevels[chan].value = 13 # Neutral DC.
      frames = framesfactory(chip)
      for frameindex, action in enumerate(frames):
        onnoteornone = action.onnoteornone()
        if onnoteornone is not None:
          chanupdaters[activechan] = Updater(onnoteornone, frameindex)
        for updater in chanupdaters:
          updater.update(frameindex)
        for b in timer.blocksforperiod(refreshrate):
          stream.call(b)
      stream.flush()
      return frames
    finally:
      di.stop()

class Boring:

  def __init__(self, nomclock):
    pass

  def update(self, chip, chan, frame):
    pass

class tone(Boring):

  def noteon(self, chip, chan):
    chip.toneflags[chan].value = True
    chip.noiseflags[chan].value = False
    chip.fixedlevels[chan].value = 15
    chip.toneperiods[chan].value = self.period

class Tone(tone):

  def __init__(self, nomclock):
    self.period = Freq(self.freq).toneperiod(nomclock)

class Noise(Note):

  def noteon(self, voladj):
    self.toneflag.value = False
    self.noiseflag.value = True
    self.setfixedlevel(15)
    self.chip.noiseperiod.value = Freq(self.freq).noiseperiod(self.nomclock)

class Both(Note):

  def noteon(self, voladj):
    self.toneflag.value = True
    self.noiseflag.value = True
    self.setfixedlevel(15)
    self.toneperiod.value = Freq(self.tfreq).toneperiod(self.nomclock)
    self.chip.noiseperiod.value = Freq(self.nfreq).noiseperiod(self.nomclock)

class Env(Note):

  def noteon(self, voladj):
    self.toneflag.value = False
    self.noiseflag.value = False
    self.levelmode.value = 1
    self.chip.envperiod.value = Freq(self.freq).envperiod(self.nomclock, self.shape)
    self.chip.envshape.value = self.shape

class All(Note):

  tfreq, nfreq, efreq, shape = 1000, 5000, 1, 0x0e

  def noteon(self, voladj):
    self.toneflag.value = True
    self.noiseflag.value = True
    self.levelmode.value = 1
    self.toneperiod.value = Freq(self.tfreq).toneperiod(self.nomclock)
    self.chip.noiseperiod.value = Freq(self.nfreq).noiseperiod(self.nomclock)
    self.chip.envperiod.value = Freq(self.efreq).envperiod(self.nomclock, self.shape)
    self.chip.envshape.value = self.shape

class PWM(Boring):

  def __init__(self, nomclock):
    self.tperiod = Freq(self.tfreq).toneperiod(nomclock)
    self.tsfreq = Fraction(self.tsfreq) # Hide the class var.

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

  def dump(self, beatsperbar, beats, name):
    def framesfactory(chip):
      timer = SimpleTimer(refreshrate)
      frames = []
      for program in beats:
        if not program:
          action = sustainaction
        else:
          note = program(self.config.nominalclock, chip, activechan, None, None)
          action = NoteAction(note)
        frames.append(action)
        b, = timer.blocksforperiod(beatsperbar)
        for _ in xrange(b.framecount - 1):
          frames.append(sustainaction)
      return frames
    path = os.path.join(self.targetpath, name)
    log.debug(path)
    start = time.time()
    config = self.config.fork()
    config.outpath = path + '.wav'
    frames = main2(framesfactory, config)
    log.info("Render of %.3f seconds took %.3f seconds.", len(frames) / refreshrate, time.time() - start)
    subprocess.check_call(['sox', path + '.wav', '-n', 'spectrogram', '-o', path + '.png'])

class NoteAction:

  def __init__(self, note):
    self.note = note

  def onnoteornone(self):
    # The note needn't know all the chip's features, so turn them off first:
    self.note.chip.flagsoff(self.note.chipchan)
    self.note.noteon(0)
    return self.note

@singleton
class sustainaction:

  def onnoteornone(self):
    pass

def main():
  config = getprocessconfig()
  config.di = DI()
  target = Target(config)
  class T250(Tone): freq = 250
  class T1k(Tone): freq = 1000
  class T1k5(Tone): freq = 1500
  class N5k(Noise): freq = 5000
  class N125k(Noise): freq = 125000
  class T1kN5k(Both): tfreq, nfreq = 1000, 5000
  class T1N5k(Both): tfreq, nfreq = config.nominalclock // 16, 5000
  class Saw600(Env): freq, shape = 600, 0x08
  class Sin600(Env): freq, shape = 600, 0x10
  class Tri650(Env): freq, shape = 650, 0x0a
  class T2k(Tone): freq = 2000
  class T3k(Tone): freq = 3000
  class T4k(Tone): freq = 4000
  class PWM501(PWM): tfreq, tsfreq = 501, 501
  class PWM250(PWM): tfreq, tsfreq = 250, 251 # Observe timer detune.
  tones = []
  for p in xrange(1, 9):
    class t(tone): period = p
    tones.append(t)
  #target.dump(2, [T250, 0, 0], 'tone250')
  #target.dump(2, [T1k, 0, 0], 'tone1k')
  #target.dump(2, [T1k5, 0, 0], 'tone1k5')
  target.dump(2, [N5k, 0, 0], 'noise5k')
  target.dump(2, [N125k, 0, 0], 'noise125k')
  target.dump(2, [T1kN5k, 0, 0], 'tone1k+noise5k')
  target.dump(2, [T1N5k, 0, 0], 'noise5k+tone1')
  target.dump(2, [Saw600, 0, 0], 'saw600')
  target.dump(2, [Sin600, 0, 0], 'sin600')
  target.dump(2, [Tri650, 0, 0], 'tri650')
  target.dump(2, [All, 0, 0], 'tone1k+noise5k+tri1')
  #target.dump(4, [T1k, T2k, T3k, T4k], 'tone1k,2k,3k,4k')
  #target.dump(2, [PWM501, 0, 0], 'pwm501')
  #target.dump(2, [PWM250, 0, 0], 'pwm250')
  #target.dump(8, tones, 'tone1-8')

if '__main__' == __name__:
  main()
