import subprocess
from nod import AbstractNode

class WavWriter(AbstractNode):

  def __init__(self, channels, infreq, signal, outfreq, path):
    AbstractNode.__init__(self)
    self.sox = subprocess.Popen([
      'sox',
      '-c', str(channels),
      '-r', str(infreq),
      '-e', 'unsigned',
      '-b', '32',
      '-t', 'raw',
      '-',
      '-r', str(outfreq),
      '-e', 'signed',
      '-b', '16',
      path,
    ], stdin = subprocess.PIPE)
    self.signal = signal

  def callimpl(self):
    self.signal(self.block).tofile(self.sox.stdin)

  def close(self):
    self.sox.stdin.close() # Send EOF.
    if self.sox.wait():
      raise Exception(self.sox.returncode)
