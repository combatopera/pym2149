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

  def __call__(self, frame):
    return self[min(frame, len(self) - 1)]
