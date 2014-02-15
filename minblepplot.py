#!/usr/bin/env python

from __future__ import division
import numpy as np
from pym2149.minblep import MinBleps

def plot(plt, mb, signal, style, padstyle):
  plt.plot(np.arange(mb.lpad), signal[:mb.lpad], padstyle)
  plt.plot(mb.lpad + np.arange(mb.kernelsize), signal[mb.lpad:-mb.rpad], style)
  plt.plot(mb.lpad + mb.kernelsize + np.arange(mb.rpad), signal[-mb.rpad:], padstyle)

def plotmin(plt, mb, shift, signal, style):
  plt.plot(mb.midpoint + shift + np.arange(len(signal)), signal, style)

def main():
  import matplotlib.pyplot as plt
  mb = MinBleps(1, 1, 5, cutoff = .5, transition = 4 / 10)
  plot(plt, mb, mb.bli * mb.scale, 'b+', 'c+')
  plot(plt, mb, mb.blep, 'bo', 'co')
  plotmin(plt, mb, 0, mb.minbli * mb.scale, 'r+')
  plotmin(plt, mb, 0, mb.minblep, 'r')
  plotmin(plt, mb, 0, mb.minblep[:mb.size], 'ro')
  plotmin(plt, mb, mb.size, mb.minblep[mb.size:], 'yo')
  plt.grid(True)
  plt.show()

if __name__ == '__main__':
  main()
