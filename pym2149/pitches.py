from buf import singleton
from pitch import Pitch

@singleton
class __all__(list):

  def __init__(self):
    for octave in xrange(10):
      for letter, offset in zip('CDEFGAB', [0, 2, 4, 5, 7, 9, 11]):
        name = "%s%s" % (letter, octave)
        globals()[name] = Pitch((1 + octave) * 12 + offset)
        self.append(name)
