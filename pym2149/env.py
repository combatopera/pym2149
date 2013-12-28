import math

class Env:

  def __init__(self, initial):
    self.levels = [initial]

  def lineto(self, hold, step, target): # TODO: Refactor to number of frames to target.
    level = self.levels[-1]
    while level != target:
      for _ in xrange(hold - 1):
        self.levels.append(level)
      sign = math.copysign(1, level - target) # Non-zero.
      level += step
      if math.copysign(1, level - target) != sign: # If same, either outcome OK.
        level = target
      self.levels.append(level)
    return self

  def __call__(self, frame):
    return self.levels[min(frame, len(self.levels) - 1)]
