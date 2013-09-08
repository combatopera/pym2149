from __future__ import division
from psg.reg import Register
from psg.osc import ToneOsc, NoiseOsc
from psg.dac import Dac
from psg.mix import BinMix, Mixer

class YM2149(Mixer):

  channels = 3

  def __init__(self):
    regtuple = lambda: tuple(Register(0) for _ in xrange(self.channels))
    self.toneperiods = regtuple()
    self.noiseperiod = Register(0)
    self.toneflags = regtuple()
    self.noiseflags = regtuple()
    self.fixedlevels = regtuple()
    self.levelmodes = regtuple()
    self.envperiod = Register(0)
    self.envshape = Register(0)
    noise = NoiseOsc(self.noiseperiod)
    # FIXME: All nodes should be called even if excluded from the mix.
    Mixer.__init__(*[self] + [Dac(BinMix(ToneOsc(self.toneperiods[i]), noise, self.toneflags[i], self.noiseflags[i]), self.levelmodes[i], self.fixedlevels[i], self.channels) for i in xrange(self.channels)])

  def update(self, frame):
    self.noiseperiod.value = frame[6] & 0x1f
    self.envperiod.value = frame[11] | (frame[12] << 8)
    self.envshape.value = frame[13] & 0x0f
    for i in xrange(self.channels):
      self.toneperiods[i].value = (frame[2 * i] & 0xff) | ((frame[2 * i + 1] & 0x0f) << 8)
      self.toneflags[i].value = frame[7] & (0x01 << i)
      self.noiseflags[i].value = frame[7] & (0x08 << i)
      self.fixedlevels[i].value = frame[8 + i] & 0x0f
      self.levelmodes[i].value = frame[8 + i] & 0x10
