from __future__ import division
from buf import singleton

class Pitch(int):

  a4freq = 440

  def freq(self):
    return Freq(self.a4freq * (2 ** ((self - 69) / 12)))

  def __add__(self, that):
    return self.__class__(int.__add__(self, that))

  def __sub__(self, that):
    return self.__class__(int.__sub__(self, that))

@singleton
class shapescale:

  trishapes = frozenset([0xa, 0xe])

  def __call__(self, shape):
    # Musically, the triangular shapes have twice the scale:
    return (256, 512)[shape in self.trishapes]

class Freq(float):

  def periodimpl(self, clock, scale):
    return Period(round(clock / (scale * self)))

  def toneperiod(self, clock):
    return self.periodimpl(clock, 16)

  def envperiod(self, clock, shape):
    return self.periodimpl(clock, shapescale(shape))

  def __mul__(self, that):
    return self.__class__(float.__mul__(self, that))

class Period(int):

  def tonefreq(self, clock):
    return Freq(clock / (16 * self))

  def envfreq(self, clock, shape):
    return Freq(clock / (shapescale(shape) * self))
