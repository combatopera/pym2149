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
