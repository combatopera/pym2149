#!/usr/bin/env python

from __future__ import division
import numpy as np
from pym2149.minblep import MinBleps

def main():
  import matplotlib.pyplot as plt
  mb = MinBleps(1, 1, 5, cutoff = .5, transition = 4 / 20)
  plt.plot(mb.bli * mb.scale, 'b+')
  plt.plot(mb.blep, 'bo')
  plt.plot(np.arange(mb.size) + mb.midpoint, mb.minbli * mb.scale, 'r+')
  for style in 'r', 'ro':
    plt.plot(np.arange(mb.size + mb.scale - 1) + mb.midpoint, mb.minblep, style)
  plt.grid(True)
  plt.show()

if __name__ == '__main__':
  main()
