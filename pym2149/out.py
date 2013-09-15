import subprocess
from nod import AbstractNode

class WavWriter(AbstractNode):

  def __init__(self, infreq, signal, outfreq, path):
    AbstractNode.__init__(self)
    self.sox = subprocess.Popen([
      'sox',
      '-c', '1',
      '-r', str(infreq),
      # Assume signal is in SoX native format:
      '-e', 'signed',
      '-b', '32',
      '-t', 'raw',
      '-',
      '-r', str(outfreq),
      '-e', 'signed',
      '-b', '16',
      path,
      # TODO: Find out whether DC filter here would be authentic.
    ], stdin = subprocess.PIPE)
    self.signal = signal

  def callimpl(self):
    self.signal(self.block).tofile(self.sox.stdin)

  def close(self):
    self.sox.stdin.close() # Send EOF.
    if self.sox.wait():
      raise Exception(self.sox.returncode)
