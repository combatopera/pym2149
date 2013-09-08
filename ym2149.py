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
    self.levels = regtuple()
    noise = NoiseOsc(self.noiseperiod)
    # FIXME: All nodes should be called even if excluded from the mix.
    Mixer.__init__(*[self] + [Dac(BinMix(ToneOsc(self.toneperiods[i]), noise, self.toneflags[i], self.noiseflags[i]), self.levels[i], 15, 13, self.channels) for i in xrange(self.channels)])

  def update(self, frame):
    self.noiseperiod.value = frame[6] & 0x1f
    for i in xrange(self.channels):
      self.toneperiods[i].value = (frame[2 * i] & 0xff) | ((frame[2 * i + 1] & 0x0f) << 8)
      self.toneflags[i].value = frame[7] & (0x01 << i)
      self.noiseflags[i].value = frame[7] & (0x08 << i)
      self.levels[i].value = frame[8 + i] & 0x0f
