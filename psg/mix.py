class Mixer:

  def __init__(self, *streams):
    self.streams = streams

  def __call__(self, buf, samplecount):
    buf = buf.tosumming(samplecount)
    for stream in self.streams:
      stream(buf, samplecount)
