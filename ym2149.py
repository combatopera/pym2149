from __future__ import division
from psg.reg import Register
from psg.osc import ToneOsc, NoiseOsc, EnvOsc
from psg.dac import Level, Dac
from psg.mix import BinMix, Mixer

class YM2149(Mixer):

  channels = 3

  def __init__(self):
    # Create registers, not quite 1-1 with the chip:
    regtuple = lambda: tuple(Register(0) for _ in xrange(self.channels))
    self.toneperiods = regtuple()
    self.noiseperiod = Register(0)
    self.toneflags = regtuple()
    self.noiseflags = regtuple()
    self.fixedlevels = regtuple()
    self.levelmodes = regtuple()
    self.envperiod = Register(0)
    self.envshape = Register(0)
    # Chip-wide signals:
    noise = NoiseOsc(self.noiseperiod)
    env = EnvOsc(self.envperiod, self.envshape)
    # Digital channels from binary to level in [0, 31]:
    channels = [ToneOsc(self.toneperiods[i]) for i in xrange(self.channels)]
    channels = [BinMix(channel, noise, self.toneflags[i], self.noiseflags[i]) for i, channel in enumerate(channels)]
    channels = [Level(self.levelmodes[i], self.fixedlevels[i], env, channel) for i, channel in enumerate(channels)]
    # FIXME: All nodes should be called even if excluded from the mix.
    Mixer.__init__(*[self] + [Dac(channel, self.channels) for i, channel in enumerate(channels)])

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
