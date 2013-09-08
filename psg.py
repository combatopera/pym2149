import math, random

psg_buf_pointer = [0] * 3
psg_tone_start_time = [0] * 3
psg_time_of_last_vbl_for_writing = 0
SCREENS_PER_SOUND_VBL = 1
PSG_CHANNEL_BUF_LENGTH = 8192 * SCREENS_PER_SOUND_VBL
VOLTAGE_FIXED_POINT = 256
PSG_CHANNEL_AMPLITUDE = 60
psg_flat_volume_level = tuple(VOLTAGE_FIXED_POINT * PSG_CHANNEL_AMPLITUDE * x / 1000 for x in [
  0, 4, 8, 12, 17, 24, 35, 48, 69, 95, 139, 191, 287, 407, 648, 1000
])
sound_freq = 50066
PSG_NOISE_ARRAY = 8192
psg_noise = tuple(random.randint(0, 1) for i in xrange(PSG_NOISE_ARRAY))
PSG_CHANNEL_BUF_LENGTH = 8192 * SCREENS_PER_SOUND_VBL
psg_channels_buf = [0] * (PSG_CHANNEL_BUF_LENGTH + 16)
fMaster = 2000000

def singleton(t):
  return t()

@singleton
class psg_reg(list):

  def __init__(self):
    list.__init__(self, [0] * 14)

  def toneperiod(self, channel):
    fine = channel * 2
    return ((self[fine + 1] & 0x0f) << 8) | (self[fine] & 0xff)

  def noiseperiod(self):
    return self[6] & 0x1f

  def mixertone(self, channel):
    return not (self[7] & (0x01 << channel))

  def mixernoise(self, channel):
    return not (self[7] & (0x08 << channel))

  def variablelevel(self, channel):
    return self[8 + channel] & 0x10

  def envelopeperiod(self):
    return ((self[12] & 0xff) << 8) | (self[11] & 0xff)

  def envelopecont(self):
    return self[13] & 0x08

  def envelopehold(self):
    return self[13] & 0x01

def psg_write_buffer(abc, to_t):
  PsgWriteBuffer()(abc, to_t)

class PsgWriteBuffer:

  noisescale = tonescale = 1 << 20
  envelopescale = 1 << 17

  def PSG_PREPARE_TONE(self, abc):
    af = self.tonescale * sound_freq * self.toneperiod * 16 / float(fMaster)
    self.tonemodulo_2 = int(af)
    bf = (self.t - psg_tone_start_time[abc]) * self.tonescale * 2
    bf = bf % (af * 2)
    af = bf - af
    if af >= 0:
      self.tonetoggle = False
      bf = af
    self.tonecountdown = self.tonemodulo_2 - int(bf)

  def PSG_PREPARE_NOISE(self):
    noiseperiod = 1 + psg_reg.noiseperiod()
    af = self.noisescale * sound_freq * noiseperiod * 16 / float(fMaster)
    self.noisemodulo = int(af)
    bf = self.t * self.noisescale
    self.noisecounter = int(math.floor(bf / af)) % PSG_NOISE_ARRAY
    bf = bf % af
    self.noisecountdown = self.noisemodulo - int(bf)
    psg_noisetoggle = psg_noise[self.noisecounter]

  def PSG_PREPARE_ENVELOPE(self):
    envperiod = max(psg_reg.envelopeperiod(), 1)
    af = self.envelopescale * sound_freq * envperiod * 256 / float(fMaster) / 32
    psg_envmodulo = int(af)
    bf = (self.t - psg_envelope_start_time) * self.envelopescale
    psg_envstage = int(math.floor(bf / af))
    bf = bf % af
    psg_envcountdown = psg_envmodulo - int(bf)
    envdeath = -1
    if (not psg_reg.envelopecont()) or psg_reg.envelopehold():
      if psg_reg[PSGR_ENVELOPE_SHAPE] == 11 or psg_reg[PSGR_ENVELOPE_SHAPE] == 13:
        envdeath = psg_flat_volume_level[15]
      else:
        envdeath = psg_flat_volume_level[0]
    envshape = psg_reg[PSGR_ENVELOPE_SHAPE] & 7
    if psg_envstage >= 32 and envdeath != -1:
      envvol = envdeath
    else:
      envvol = psg_envelope_level[envshape][psg_envstage & 63]

  def PSG_TONE_ADVANCE(self):
    self.tonecountdown -= self.tonescale * 2
    while self.tonecountdown < 0:
      self.tonecountdown += self.tonemodulo_2
      self.tonetoggle = not self.tonetoggle

  def PSG_NOISE_ADVANCE(self):
    self.noisecountdown -= self.noisescale
    while self.noisecountdown < 0:
      self.noisecountdown += self.noisemodulo
      self.noisecounter += 1
      if self.noisecounter >= PSG_NOISE_ARRAY:
        self.noisecounter = 0
      psg_noisetoggle = psg_noise[self.noisecounter]

  def PSG_ENVELOPE_ADVANCE(self):
    psg_envcountdown -= TWO_TO_SEVENTEEN
    while psg_envcountdown < 0:
      psg_envcountdown += psg_envmodulo
      psg_envstage += 1
      if psg_envstage >= 32 and envdeath != -1:
        envvol = envdeath
      else:
        envvol = psg_envelope_level[envshape][psg_envstage & 63]

  def __call__(self, abc, to_t):
    # buffer starts at time time_of_last_vbl
    # we've written up to psg_buf_pointer[abc]
    # so start at pointer and write to to_t,
    self.tonemodulo_2 = self.noisemodulo = None
    self.tonecountdown = self.noisecountdown = None
    self.noisecounter = None
    self.tonetoggle = True
    psg_noisetoggle = None
    q = psg_buf_pointer[abc]
    self.t = psg_time_of_last_vbl_for_writing + psg_buf_pointer[abc]
    to_t = max(to_t, self.t)
    to_t = min(to_t, psg_time_of_last_vbl_for_writing + PSG_CHANNEL_BUF_LENGTH)
    count = max(min(int(to_t - self.t), PSG_CHANNEL_BUF_LENGTH - psg_buf_pointer[abc]), 0)
    self.toneperiod = psg_reg.toneperiod(abc)
    if not psg_reg.variablelevel(abc):
      vol = psg_flat_volume_level[psg_reg[abc + 8] & 15]
      if psg_reg.mixertone(abc) and self.toneperiod > 9: # tone enabled
        self.PSG_PREPARE_TONE(abc)
        if psg_reg.mixernoise(abc):
          self.PSG_PREPARE_NOISE()
          while count > 0:
            if not (self.tonetoggle or psg_noisetoggle):
              psg_channels_buf[q] += vol
            q += 1
            self.PSG_TONE_ADVANCE()
            self.PSG_NOISE_ADVANCE()
            count -= 1
        else: # tone only
          while count > 0:
            if not self.tonetoggle:
              psg_channels_buf[q] += vol
            q += 1
            self.PSG_TONE_ADVANCE()
            count -= 1
      elif psg_reg.mixernoise(abc):
        self.PSG_PREPARE_NOISE()
        while count > 0:
          if not psg_noisetoggle:
            psg_channels_buf[q] += vol
          q += 1
          self.PSG_NOISE_ADVANCE()
          count -= 1
      else: # nothing enabled
        while count > 0:
          psg_channels_buf[q] += vol
          q += 1
          count -= 1
    else:
      envdeath = psg_envstage = envshape = None
      psg_envmodulo = envvol = psg_envcountdown = None
      self.PSG_PREPARE_ENVELOPE()
      if psg_reg.mixertone(abc) and self.toneperiod > 9: # tone enabled
        self.PSG_PREPARE_TONE(abc)
        if psg_reg.mixernoise(abc):
          self.PSG_PREPARE_NOISE()
          while count > 0:
            if not (self.tonetoggle or psg_noisetoggle):
              psg_channels_buf[q] += envvol
            q += 1
            self.PSG_TONE_ADVANCE()
            self.PSG_NOISE_ADVANCE()
            self.PSG_ENVELOPE_ADVANCE()
            count -= 1
        else: # tone only
          while count > 0:
            if not self.tonetoggle:
              psg_channels_buf[q] += envvol
            q += 1
            self.PSG_TONE_ADVANCE()
            self.PSG_ENVELOPE_ADVANCE()
            count -= 1
      elif psg_reg.mixernoise(abc):
        self.PSG_PREPARE_NOISE()
        while count > 0:
          if not psg_noisetoggle:
            psg_channels_buf[q] += envvol
          q += 1
          self.PSG_NOISE_ADVANCE()
          self.PSG_ENVELOPE_ADVANCE()
          count -= 1
      else: # nothing enabled
        while count > 0:
          psg_channels_buf[q] += envvol
          q += 1
          self.PSG_ENVELOPE_ADVANCE()
          count -= 1
    psg_buf_pointer[abc] = to_t - psg_time_of_last_vbl_for_writing

if '__main__' == __name__:
  psg_reg[8] = 15
  psg_reg[0] = 255
  psg_write_buffer(0, PSG_CHANNEL_BUF_LENGTH)
  print psg_channels_buf
