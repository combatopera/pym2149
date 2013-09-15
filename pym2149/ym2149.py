from reg import Reg, DerivedReg
from osc import ToneOsc, NoiseOsc, EnvOsc
from dac import Level, Dac
from mix import BinMix, Mixer

stclock = 2000000

class Registers:

  channels = 3

  def __init__(self):
    self.R = tuple(Reg(0) for i in xrange(16))
    # Clamping is authentic in all 3 cases, see qtonpzer, qnoispec, qenvpzer respectively.
    # TP, NP, EP are suitable for plugging into the formulas in the datasheet:
    TP = lambda f, r: max(1, ((r & 0x0f) << 8) | (f & 0xff))
    NP = lambda p: max(1, p & 0x1f)
    EP = lambda f, r: max(1, ((r & 0xff) << 8) | (f & 0xff))
    self.toneperiods = tuple(DerivedReg(TP, self.R[c * 2], self.R[c * 2 + 1]) for c in xrange(self.channels))
    self.noiseperiod = DerivedReg(NP, self.R[0x6])
    def flagxform(b):
      mask = 0x01 << b
      return lambda x: not (x & mask)
    self.toneflags = tuple(DerivedReg(flagxform(c), self.R[0x7]) for c in xrange(self.channels))
    self.noiseflags = tuple(DerivedReg(flagxform(self.channels + c), self.R[0x7]) for c in xrange(self.channels))
    self.fixedlevels = tuple(DerivedReg(lambda x: x & 0x0f, self.R[0x8 + c]) for c in xrange(self.channels))
    self.levelmodes = tuple(DerivedReg(lambda x: x & 0x10, self.R[0x8 + c]) for c in xrange(self.channels))
    self.envperiod = DerivedReg(EP, self.R[0xB], self.R[0xC])
    self.envshape = DerivedReg(lambda x: x & 0x0f, self.R[0xD])

class YM2149(Registers, Mixer):

  def __init__(self, ampshare = None):
    Registers.__init__(self)
    # Chip-wide signals:
    noise = NoiseOsc(self.noiseperiod)
    env = EnvOsc(self.envperiod, self.envshape)
    # Digital channels from binary to level in [0, 31]:
    channels = [ToneOsc(self.toneperiods[i]) for i in xrange(self.channels)]
    channels = [BinMix(channel, noise, self.toneflags[i], self.noiseflags[i]) for i, channel in enumerate(channels)]
    channels = [Level(self.levelmodes[i], self.fixedlevels[i], env, channel) for i, channel in enumerate(channels)]
    if ampshare is None:
      ampshare = self.channels
    # FIXME: All nodes should be called even if excluded from the mix.
    # TODO: The real thing has separate outputs, so analog mixer should be optional.
    Mixer.__init__(*[self] + [Dac(channel, ampshare) for i, channel in enumerate(channels)])

  def update(self, frame):
    for i, x in enumerate(frame):
      if 0xD != i or 255 != x:
        self.R[i].value = x
