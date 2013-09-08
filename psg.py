import math

psg_buf_pointer = [0] * 3
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

def singleton(t):
  return t()

@singleton
class psg_reg(list):

  def __init__(self):
    list.__init__(self, [0] * 14)

  def noiseperiod(self):
    return self[6] & 0x1f

  def mixertone(self, channel):
    return not (self[7] & (0x01 << channel))

  def mixernoise(self, channel):
    return not (self[7] & (0x08 << channel))

  def variablelevel(self, channel):
    return self[8 + channel] & 0x10

def psg_write_buffer(abc, to_t):
  # buffer starts at time time_of_last_vbl
  # we've written up to psg_buf_pointer[abc]
  # so start at pointer and write to to_t,
  psg_tonemodulo_2 = psg_noisemodulo = None
  psg_tonecountdown = psg_noisecountdown = None
  psg_noisecounter = None
  af = bf = None
  psg_tonetoggle = True
  psg_noisetoggle = None
  q = psg_buf_pointer[abc]
  t = psg_time_of_last_vbl_for_writing + psg_buf_pointer[abc]
  to_t = max(to_t, t)
  to_t = min(to_t, psg_time_of_last_vbl_for_writing + PSG_CHANNEL_BUF_LENGTH)
  count = max(min(int(to_t - t), PSG_CHANNEL_BUF_LENGTH - psg_buf_pointer[abc]), 0)
  toneperiod = ((int(psg_reg[abc * 2 + 1]) & 0xf) << 8) + psg_reg[abc * 2]
  def PSG_PREPARE_TONE():
    af = int(toneperiod) * sound_freq
    af *= float(1 << 17) / 15625
    psg_tonemodulo_2 = int(af)
    bf = t - psg_tone_start_time[abc]
    bf *= float(1 << 21)
    bf = bf % (af * 2)
    af = bf - af
    if af >= 0:
      psg_tonetoggle = False
      bf = af
    psg_tonecountdown = psg_tonemodulo_2 - int(bf)
  def PSG_PREPARE_NOISE():
    noiseperiod = 1 + psg_reg.noiseperiod()
    af = int(noiseperiod) * sound_freq
    af *= float(1 << 17) / 15625
    psg_noisemodulo = int(af)
    bf = t
    bf *= float(1 << 20)
    psg_noisecounter = int(math.floor(bf / af))
    psg_noisecounter &= (PSG_NOISE_ARRAY - 1)
    bf = bf % af
    psg_noisecountdown = psg_noisemodulo - int(bf)
    psg_noisetoggle = psg_noise[psg_noisecounter]
  def PSG_PREPARE_ENVELOPE():
    envperiod = max((int(psg_reg[PSGR_ENVELOPE_PERIOD_HIGH]) << 8) + psg_reg[PSGR_ENVELOPE_PERIOD_LOW], 1)
    af = envperiod
    af *= sound_freq
    af *= float(1 << 13) / 15625
    psg_envmodulo = int(af)
    bf = t - psg_envelope_start_time
    bf *= float(1 << 17)
    psg_envstage = int(math.floor(bf / af))
    bf = bf % af
    psg_envcountdown = psg_envmodulo - int(bf)
    envdeath = -1
    if (psg_reg[PSGR_ENVELOPE_SHAPE] & PSG_ENV_SHAPE_CONT) == 0 or (psg_reg[PSGR_ENVELOPE_SHAPE] & PSG_ENV_SHAPE_HOLD):
      if psg_reg[PSGR_ENVELOPE_SHAPE] == 11 or psg_reg[PSGR_ENVELOPE_SHAPE] == 13:
        envdeath = psg_flat_volume_level[15]
      else:
        envdeath = psg_flat_volume_level[0]
    envshape = psg_reg[PSGR_ENVELOPE_SHAPE] & 7
    if psg_envstage >= 32 and envdeath != -1:
      envvol = envdeath
    else:
      envvol = psg_envelope_level[envshape][psg_envstage & 63]
  def PSG_TONE_ADVANCE():
    psg_tonecountdown -= TWO_MILLION
    while psg_tonecountdown < 0:
      psg_tonecountdown += psg_tonemodulo_2
      psg_tonetoggle = not psg_tonetoggle
  def PSG_NOISE_ADVANCE():
    psg_noisecountdown -= ONE_MILLION
    while psg_noisecountdown < 0:
      psg_noisecountdown += psg_noisemodulo
      psg_noisecounter += 1
      if psg_noisecounter >= PSG_NOISE_ARRAY:
        psg_noisecounter = 0
      psg_noisetoggle = psg_noise[psg_noisecounter]
  def PSG_ENVELOPE_ADVANCE():
    psg_envcountdown -= TWO_TO_SEVENTEEN
    while psg_envcountdown < 0:
      psg_envcountdown += psg_envmodulo
      psg_envstage += 1
      if psg_envstage >= 32 and envdeath != -1:
        envvol = envdeath
      else:
        envvol = psg_envelope_level[envshape][psg_envstage & 63]
  if not psg_reg.variablelevel(abc):
    vol = psg_flat_volume_level[psg_reg[abc + 8] & 15]
    if psg_reg.mixertone(abc) and toneperiod > 9: # tone enabled
      PSG_PREPARE_TONE()
      if psg_reg.mixernoise(abc):
        PSG_PREPARE_NOISE()
        while count > 0:
          if not (psg_tonetoggle or psg_noisetoggle):
            psg_channels_buf[q] += vol
          q += 1
          PSG_TONE_ADVANCE()
          PSG_NOISE_ADVANCE()
          count -= 1
      else: # tone only
        while count > 0:
          if not psg_tonetoggle:
            psg_channels_buf[q] += vol
          q += 1
          PSG_TONE_ADVANCE()
          count -= 1
    elif psg_reg.mixernoise(abc):
      PSG_PREPARE_NOISE()
      while count > 0:
        if not psg_noisetoggle:
          psg_channels_buf[q] += vol
        q += 1
        PSG_NOISE_ADVANCE()
        count -= 1
    else: # nothing enabled
      while count > 0:
        psg_channels_buf[q] += vol
        q += 1
        count -= 1
  else:
    envdeath = psg_envstage = envshape = None
    psg_envmodulo = envvol = psg_envcountdown = None
    PSG_PREPARE_ENVELOPE()
    if psg_reg.mixertone(abc) and toneperiod > 9: # tone enabled
      PSG_PREPARE_TONE()
      if psg_reg.mixernoise(abc):
        PSG_PREPARE_NOISE()
        while count > 0:
          if not (psg_tonetoggle or psg_noisetoggle):
            psg_channels_buf[q] += envvol
          q += 1
          PSG_TONE_ADVANCE()
          PSG_NOISE_ADVANCE()
          PSG_ENVELOPE_ADVANCE()
          count -= 1
      else: # tone only
        while count > 0:
          if not psg_tonetoggle:
            psg_channels_buf[q] += envvol
          q += 1
          PSG_TONE_ADVANCE()
          PSG_ENVELOPE_ADVANCE()
          count -= 1
    elif psg_reg.mixernoise(abc):
      PSG_PREPARE_NOISE()
      while count > 0:
        if not psg_noisetoggle:
          psg_channels_buf[q] += envvol
        q += 1
        PSG_NOISE_ADVANCE()
        PSG_ENVELOPE_ADVANCE()
        count -= 1
    else: # nothing enabled
      while count > 0:
        psg_channels_buf[q] += envvol
        q += 1
        PSG_ENVELOPE_ADVANCE
        count -= 1
  psg_buf_pointer[abc] = to_t - psg_time_of_last_vbl_for_writing
