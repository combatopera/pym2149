from __future__ import division
from nod import Block

def blocks(clock, refreshrate, secondsornone = None):
  if secondsornone is None:
    acceptframeindex = lambda: True
    clamp = lambda: blocksize
  else:
    framecount = int(round(secondsornone * clock))
    acceptframeindex = lambda: frameindex < framecount
    clamp = lambda: min(framecount - frameindex, blocksize)
  frameindex = 0
  carry = 0
  while acceptframeindex():
    blocksize = clock // refreshrate
    carry += clock % refreshrate # Adjustment strictly less than refreshrate.
    if carry >= refreshrate: # Shouldn't be True again after the body.
      blocksize += 1
      carry -= refreshrate
    blocksize = clamp()
    yield Block(blocksize)
    frameindex += blocksize
