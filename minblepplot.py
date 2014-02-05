#!/usr/bin/env python

from __future__ import division
import numpy as np
from minblep import MinBleps

def main():
  import matplotlib.pyplot as plt
  minbleps = MinBleps(5, cutoff = .5, transition = 4 / 20)
  plt.plot(minbleps.bli * minbleps.scale, 'b+')
  plt.plot(minbleps.blep, 'bo')
  plt.plot(np.arange(minbleps.size) + minbleps.midpoint, minbleps.minbli * minbleps.scale, 'r+')
  for style in 'r', 'ro':
    plt.plot(np.arange(minbleps.size) + minbleps.midpoint, minbleps.minblep, style)
  plt.grid(True)
  plt.show()

if __name__ == '__main__':
  main()
