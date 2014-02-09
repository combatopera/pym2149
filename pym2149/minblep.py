from __future__ import division
import numpy as np, fractions

class MinBleps:

  def __init__(self, ctrlrate, outrate, scale, cutoff = .475, transition = .05):
    # Closest even order to 4/transition:
    order = int(round(4 / transition / 2)) * 2
    self.midpoint = order * scale // 2 # Index of peak of sinc.
    self.size = order * scale + 1
    x = (np.arange(self.size) / (self.size - 1) * 2 - 1) * order * cutoff
    # If cutoff is .5 the sinc starts and ends with zero.
    # The window is necessary for a reliable integral height later:
    self.bli = np.blackman(self.size) * np.sinc(x) / scale * cutoff * 2
    self.blep = np.cumsum(self.bli)
    # Everything is real after we discard the phase info here:
    absdft = np.abs(np.fft.fft(self.bli))
    realcepstrum = np.fft.ifft(np.log(absdft)) # Symmetric apart from first element.
    # Leave first point, zero max phase part, double min phase part to compensate:
    realcepstrum[1:self.midpoint + 1] *= 2
    realcepstrum[self.midpoint + 1:] = 0
    self.minbli = np.fft.ifft(np.exp(np.fft.fft(realcepstrum))).real
    dtype = np.float32
    self.minblep = np.append(np.cumsum(self.minbli, dtype = dtype), [1] * (scale - 1))
    self.minbleps = np.reshape(self.minblep, (scale, order + 1), 'F')
    self.idealscale = ctrlrate // fractions.gcd(ctrlrate, outrate)
    self.factor = outrate / ctrlrate * scale
    self.mixinsize = len(self.minblep[::scale])
    self.scale = scale

  def getoutindexandshape(self, ctrlx):
    tmpi = np.array(ctrlx * self.factor + .5, dtype = int)
    outi = (tmpi + self.scale - 1) // self.scale
    shape = outi * self.scale - tmpi
    return outi, shape

  def getmixin(self, shape, amp):
    return np.transpose(np.transpose(self.minbleps[shape]) * amp)
