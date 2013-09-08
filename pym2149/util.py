from __future__ import division
from nod import Block

def blocks(clock, refreshrate, seconds):
  framecount = int(round(seconds * clock))
  frameindex = 0
  carry = 0
  while frameindex < framecount:
    blocksize = min(framecount - frameindex, clock // refreshrate)
    carry += clock % refreshrate
    while carry >= refreshrate: # Probably at most once.
      blocksize += 1
      carry -= refreshrate
    yield Block(blocksize)
    frameindex += blocksize
