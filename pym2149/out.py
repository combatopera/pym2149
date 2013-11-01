import subprocess
from nod import AbstractNode

class WavWriter(AbstractNode):

  def __init__(self, clock, chip, path):
    AbstractNode.__init__(self)
    channels = 1
    outfreq = 44100
    command = [
      'sox',
      '-c', str(channels),
      '-r', str(clock),
      # Assume signal is in SoX native format:
      '-e', 'signed',
      '-b', '32',
      '-t', 'raw',
      '-',
      # TODO LATER: Output format should be configurable.
      '-r', str(outfreq),
      '-e', 'signed',
      '-b', '16',
    ]
    if '-' == path:
      command += ['-t', 'wav']
    command += [path]
    # TODO: Find out whether a DC filter would be authentic.
    self.sox = subprocess.Popen(command, stdin = subprocess.PIPE)
    self.chip = chip

  def callimpl(self):
    self.chain(self.chip).tofile(self.sox.stdin)

  def flush(self):
    if self.sox is not None:
      self.sox.stdin.close() # Send EOF.
      status = self.sox.wait()
      self.sox = None # We have released the resource(s).
      if status:
        raise Exception(status)

  def close(self):
    self.flush() # Does nothing if flush already called.
