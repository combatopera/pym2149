import subprocess

class WavWriter:

  def __init__(self, channels, infreq, outfreq, path):
    self.sox = subprocess.Popen([
      'sox',
      '-c', str(channels),
      '-r', str(infreq),
      '-e', 'floating-point',
      '-b', '64',
      '-t', 'raw',
      '-',
      '-r', str(outfreq),
      '-e', 'signed',
      '-b', '16',
      path,
    ], stdin = subprocess.PIPE)

  def __call__(self, buf, framecount):
    buf.tofile(0, framecount, self.sox.stdin)

  def close(self):
    self.sox.stdin.close() # Send EOF.
    if self.sox.wait():
      raise Exception(self.sox.returncode)
