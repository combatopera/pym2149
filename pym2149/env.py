from __future__ import division

class Env(list):

  def __init__(self, initial):
    self.append(initial)

  def lin(self, n, target):
    source = self[-1]
    for i in xrange(1, n + 1):
      self.append(int(round(source + (target - source) * i / n)))
    return self

  def jump(self, target):
    self[-1] = target
    return self

  def hold(self, n):
    return self.lin(n, self[-1])

  def tri(self, n, target, waves):
    source = self[-1]
    for _ in xrange(waves):
      self.lin(n, target)
      self.lin(n * 2, source * 2 - target)
      self.lin(n, source)
    return self

  def __call__(self, frame):
    return self[min(frame, len(self) - 1)]
