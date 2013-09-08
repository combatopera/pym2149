#!/usr/bin/env python

import sys, struct

class YM6File:

  magic = 'YM6!LeOnArD!'
  wordstruct = struct.Struct('>H')
  lwordstruct = struct.Struct('>I')
  framesize = 16

  def __init__(self, f):
    if self.magic != f.read(len(self.magic)):
      raise Exception('Bad magic.')
    self.f = f
    self.framecount = self.lword()

  def word(self):
    return self.wordstruct.unpack(self.f.read(2))[0]

  def lword(self):
    return self.lwordstruct.unpack(self.f.read(4))[0]

  def skip(self, n):
    self.f.seek(n, 1)

  def ntstring(self):
    start = self.f.tell()
    while ord(self.f.read(1)):
      pass
    textlen = self.f.tell() - 1 - start
    self.f.seek(start)
    text = self.f.read(textlen)
    self.skip(1)
    return text

  def frame(self):
    v = [None] * self.framesize
    for i in xrange(self.framesize - 1):
      v[i] = ord(self.f.read(1))
      self.f.seek(-1 + self.framecount, 1)
    v[self.framesize - 1] = ord(self.f.read(1))
    self.f.seek(-(self.framesize - 1) * self.framecount, 1)
    return v

  def close(self):
    self.f.close()

def main():
  path, = sys.argv[1:]
  f = open(path, 'rb')
  try:
    f = YM6File(f)
    f.lword() # Song attributes.
    samplecount = f.word()
    clock = f.lword()
    framefreq = f.word()
    loopframe = f.lword()
    f.skip(f.word()) # Future expansion.
    for sampleindex in xrange(samplecount):
      f.skip(f.lword())
    for _ in xrange(3):
      print >> sys.stderr, f.ntstring()
    for frameindex in xrange(f.framecount):
      print f.frame()
  finally:
    f.close()

if '__main__' == __name__:
  main()
