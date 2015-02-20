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
from pym2149.iface import Stream
from pym2149.program import Note
from pym2149.channels import Channels
from ymplayer import ChipTimer
import os, subprocess, time

log = logging.getLogger(__name__)

refreshrate = 60 # Deliberately not a divisor of the clock.

def main2(frames, config, programids):
    midichan = config.midichannelbase
    di = createdi(config)
    configure(di)
    di.add(Channels)
    di.start()
    try:
      di.add(ChipTimer)
      timer = di(Timer)
      stream = di(Stream)
      channels = di(Channels)
      channels.programchange(0, midichan, programids[Silence])
      # Play silence on all chip channels:
      for chan in xrange(config.chipchannels):
        channels.noteon(0, midichan, 60 + chan, config.neutralvelocity)
      for chan in xrange(config.chipchannels):
        channels.noteoff(0, midichan, 60 + chan, config.neutralvelocity)
      for frameindex, program in enumerate(frames):
        if program:
          channels.programchange(frameindex, midichan, programids[program])
          channels.noteon(frameindex, midichan, 60, config.neutralvelocity)
        channels.updateall(frameindex)
        for b in timer.blocksforperiod(refreshrate):
          stream.call(b)
      stream.flush()
    finally:
      di.stop()

class Silence(Note):

  def noteon(self, voladj):
    self.setfixedlevel(13) # Neutral DC.

class BaseTone(Note):

  def noteon(self, voladj):
    self.toneflag.value = True
    self.setfixedlevel(15)
    self.toneperiod.value = self.period

class Tone(BaseTone):

  def noteon(self, voladj):
    self.period = Freq(self.freq).toneperiod(self.nomclock)
    BaseTone.noteon(self, voladj)

class Noise(Note):

  def noteon(self, voladj):
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

class PWM(Note):

  def noteon(self, voladj):
    self.toneflag.value = True
    self.chip.tsflags[self.chipchan].value = True
    self.setfixedlevel(15)
    self.toneperiod.value = Freq(self.tfreq).toneperiod(self.nomclock)
    self.chip.tsfreqs[self.chipchan].value = Fraction(self.tsfreq)

class Target:

  def __init__(self, config):
    self.targetpath = os.path.join(os.path.dirname(__file__), 'target')
    if not os.path.exists(self.targetpath):
      os.mkdir(self.targetpath)
    self.config = config

  def dump(self, beatsperbar, beats, name):
    config = self.config.fork()
    programids = {}
    config.midiprograms = {}
    config.midichanneltoprogram = {} # We'll use programchange as necessary.
    def register(program):
      programid = config.midiprogrambase + len(programids)
      config.midiprograms[programid] = program
      programids[program] = programid
    register(Silence)
    timer = SimpleTimer(refreshrate)
    frames = []
    for program in beats:
      if program and program not in programids:
        register(program)
      frames.append(program)
      b, = timer.blocksforperiod(beatsperbar)
      for _ in xrange(b.framecount - 1):
        frames.append(0)
    path = os.path.join(self.targetpath, name)
    log.debug(path)
    start = time.time()
    config.outpath = path + '.wav'
    main2(frames, config, programids)
    log.info("Render of %.3f seconds took %.3f seconds.", len(frames) / refreshrate, time.time() - start)
    subprocess.check_call(['sox', path + '.wav', '-n', 'spectrogram', '-o', path + '.png'])

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
    class t(BaseTone): period = p
    tones.append(t)
  target.dump(2, [T250, 0, 0], 'tone250')
  target.dump(2, [T1k, 0, 0], 'tone1k')
  target.dump(2, [T1k5, 0, 0], 'tone1k5')
  target.dump(2, [N5k, 0, 0], 'noise5k')
  target.dump(2, [N125k, 0, 0], 'noise125k')
  target.dump(2, [T1kN5k, 0, 0], 'tone1k+noise5k')
  target.dump(2, [T1N5k, 0, 0], 'noise5k+tone1')
  target.dump(2, [Saw600, 0, 0], 'saw600')
  target.dump(2, [Sin600, 0, 0], 'sin600')
  target.dump(2, [Tri650, 0, 0], 'tri650')
  target.dump(2, [All, 0, 0], 'tone1k+noise5k+tri1')
  target.dump(4, [T1k, T2k, T3k, T4k], 'tone1k,2k,3k,4k')
  target.dump(2, [PWM501, 0, 0], 'pwm501')
  target.dump(2, [PWM250, 0, 0], 'pwm250')
  target.dump(8, tones, 'tone1-8')

if '__main__' == __name__:
  main()
