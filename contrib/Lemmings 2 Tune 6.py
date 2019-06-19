from pym2149.lc import V, D, E, naturalminor, unit
from pym2149.pitches import B3, C2

class CommonDrum:

    level = V('2x15 2x14,0')
    tf = nf = V('4x1,0')

    def _on(self, frame, chip, np):
        if frame >= 4:
            return
        chip.fixedlevel = self.level[frame]
        chip.noiseflag = self.nf[frame]
        chip.toneflag = self.tf[frame]
        if chip.noiseflag and not any(channel.noiseflag for channel in chip[1:]):
            chip.noiseperiod = np
        return True

class Kick(CommonDrum):

    pitch = C2 - .11

    def on(self, frame, chip):
        if super()._on(frame, chip, 21):
            chip.tonepitch = self.pitch

class Snare(CommonDrum):

    pitch = V('2x60.04 55.06 51.19')

    def on(self, frame, chip):
        if super()._on(frame, chip, 21):
            chip.tonepitch = self.pitch[frame]

class Boop(CommonDrum):

    basedegree = D('++')

    def on(self, frame, chip, degree, attenuation = V('0'), np = V('21')):
        if super()._on(frame, chip, np[0]):
            chip.fixedlevel -= attenuation[0]
            chip.tonepitch = chip.topitch((self.basedegree + degree)[0])

class Fill(Boop):

    def on(self, frame, chip, degree):
        chip.fixedlevel = 0
        chip.noiseflag = False
        chip.toneflag = False
        super().on(frame, chip, degree, np = V('1'))

class Side:

    level = V('15//6,12')
    tf = nf = V('8x1,0')
    np = 21

    def on(self, frame, chip, degree):
        if frame >= 8:
            return
        chip.fixedlevel = self.level[frame]
        chip.noiseflag = self.nf[frame]
        chip.toneflag = self.tf[frame]
        if chip.noiseflag and not any(channel.noiseflag for channel in chip[1:]):
            chip.noiseperiod = self.np
        chip.tonepitch = chip.topitch(degree[0])

class Open:

    level = V('15//6,12')
    nf = V('8x1,0')

    def on(self, frame, chip, attenuation = V('0'), np = V('1')):
        if frame >= 8:
            return
        chip.fixedlevel = self.level[frame] - attenuation[0]
        chip.noiseflag = self.nf[frame]
        chip.toneflag = False
        if chip.noiseflag:
            chip.noiseperiod = np[0]

class Bass:

    levels = V('15//6 2x13,0'), V('4x15 4x14,0')
    tf = V('8x1,0')
    basedegree = D('-')

    def on(self, frame, chip, degree, velocity):
        chip.fixedlevel = self.levels[round(velocity[0])][frame]
        chip.noiseflag = False
        chip.toneflag = self.tf[frame]
        chip.tonepitch = chip.topitch((self.basedegree + degree)[0])

class Lead:

    levels = V('4x15 17x14 6x13,12'), V('4x15,14'), V('4x15,14')
    offlevel = V('5x14 13//24,9')
    vibs = V('0'), V('0'), V('7.5x /3.5,.30/7 -.30/7')

    def _common(self, frame, chip, degree, velocity, slide):
        velocity = round(velocity[0])
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[frame * slide[0]]) + self.vibs[velocity][frame]
        return velocity

    def on(self, frame, chip, degree, velocity, slide):
        velocity = self._common(frame, chip, degree, velocity, slide)
        chip.fixedlevel = self.levels[velocity][frame]

    def off(self, frame, chip, degree, velocity, slide, onframes):
        self._common(frame, chip, degree, velocity, slide)
        chip.fixedlevel = self.offlevel[frame - onframes]

class Tone:

    level = V('15//15,10')

    def on(self, frame, chip, degree):
        chip.fixedlevel = self.level[frame]
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[0])

class Ping:

    levels = V('12//16,8'), V('14//16,10')

    def on(self, frame, chip, degree, velocity):
        chip.fixedlevel = self.levels[round(velocity[0])][frame]
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[0])

class Diarp:

    def on(self, frame, chip, degree0, degree1, level):
        chip.fixedlevel = level[0]
        chip.noiseflag = False
        chip.toneflag = True
        degree = degree0 if frame % 8 < 4 else degree1
        chip.tonepitch = chip.topitch(degree[0])

class Ramp:

    level = V('4x15,14')
    tp = V('-4/4 /4') * V('/128 64')
    vib = .06

    def on(self, frame, chip, degree):
        chip.fixedlevel = self.level[frame]
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[0]) + self.vib
        chip.toneperiod += self.tp[frame]

def lead1(lastoff):
    return E(Lead, "3x2 2x|4x 2 2x|2 1.5 .5 4x|2 1.5 .5 4x|3x2 2x|4x 4/%s" % lastoff,
            degree = D('2x3 2x2 3x 2|3 5 2 3 2x 3 4|3.5x5 .5x6 5 4/.5 2 3|3.5x4 .5x5 4 3/.5 1 2|2x3 2x2 3x 2|3 5/.25 2 3 4x'),
            velocity = V('18x 1.5x1 6.5x 1.5x1 4.5x|12x 4x1'),
            slide = V('16x|5x 1 2x|5x 1 2x|8x|0 1 6x'))

snare1 = E(Snare, '.5 1 .5 1 .5 1 2x.25 6x.5')
snare2 = E(Snare, '/3.5 4.5')
bass1 = E(Bass, '4x1.5 2x',
        degree = D('7x- 7--'),
        velocity = V('0'))
bass2 = E(Bass, '1 2x.5 2x',
        degree = D('1 ++/.5 5- 7|1 .5x++ .5x+ 5- 7'),
        velocity = V('1'))
bass3 = bass2 | E(Bass, '1 2x.5 2x',
        degree = D('6- 6/.5 3- 3|6- 6/.5 3- 3|4- 4/.5 1 4|4- 4/.5 1 4|7- 7/.5 4 7|7- 7/.5 4 7'),
        velocity = V('1'))
bass4 = bass2 | E(Bass, '1 2x.5 2x',
        degree = D('6- 6/.5 3- 3|6- 6/.5 3- 6|1 ++/.5 5- 7|1 .5x++ .5x+ 5- 7|7- 7/.5 4 7|7- 7/.5 4 7'),
        velocity = V('1'))
ramp = E(Ramp, '8',
        degree = D('4'))
diarp = E(Diarp, '8x4',
        degree0 = D('4x3+ 4x2+'),
        degree1 = D('+'),
        level = V('16x15 14/12 4x11'))
boop1 = E(Boop, '/3.5 2x2 .5',
        degree = D('3'))
boop2 = E(Boop, '/11.5 1 2x.5 1 3x.5',
        degree = D('26x3 5 3x3 5 3').of(.5))
boop3 = E(Boop, '.5',
        degree = D('3 5').of(.5),
        attenuation = V('3 4').of(.5))
boop4 = E(Boop, '.5',
        degree = D('3 5').of(.5),
        attenuation = V('4 5').of(.5))
kick = E(Kick, '2')
side1 = E(Side, '/1 2x.5 /6',
        degree = D('1'))
side2 = E(Side, '/1 2x.5 /3 2x.5 /2|/1 2x.5 /6',
        degree = D('7- 4x 3x7-'))
side3 = E(Side, '/1 2x.5 /2',
        degree = D('1'))
side4 = E(Side, '2x .5 1 .5 2x .5 1 .5 2x .5 1 .5 8x.5',
        degree = D('++') + D('4x 7- 2x 7- 4x 7- 2x 7- 4x 7- 2x 7- 3 2 1 7- 3 2 1 7-').of(.5))
open1 = E(Open, '.5/.5 2 .5 2x2 1')
open2 = E(Open, '.5/.5 2.5 4 2x.5|.5/.5 2.5 5')
open3 = E(Open, '.5/.5 2 .5 1.5 2 3x.5')
open4 = E(Open, '.5',
        attenuation = V('1 3 2 1 3 2 1 3 2 1 3 2 1 3 2 4').of(.5),
        np = V('2x1 4x21 1 7x21 2x1').of(.5))
lead2 = E(Tone, '2/1 1 4x.5 3x|2/1 1 4x.5 3x|2/1 1 4x.5 3x|2x2/1 4x',
        degree = D('-') + D('2x 1.5x3/.5 .5x2 .5x3 .5x2 3 1 7-|2x6- 1.5x/.5 .5x7- .5x .5x7- 1 6- 5-|2x4- 1.5x6#-/.5 .5x6- .5x6#- .5x6- 6#- 4- 6#-|2x7- 2x 2 7- 1 2'))
lead3 = E(Lead, '6 1 3 1 3 1 3 1 3 2|4 /4',
        degree = D('+') + D('6x/.5 3 3x2 3 3x/.5 3 3x2 3 3x4 2x|8x2'),
        velocity = V('2'),
        slide = V('6x1 5x 3x1 18x'))
lead4 = E(Ping, '2/1 1 4x.5 3x|2/1 1 4x.5 3x|2/1 1 4x.5 3x|2/1 6/5',
        degree = D('++') + D('2x 1.5x3/.5 .5x2 .5x3 .5x2 3 1 7-|2x6- 1.5x3/.5 .5x2 .5x3 .5x2 3 1 7-|2x 1.5x3/.5 .5x2 .5x3 .5x2 2x3 1|8x2'),
        velocity = V('26x1 6x'))
fill = E(Fill, '/28 8x.5',
        degree = D('3 2').of(.5))
A = snare1, bass1 * 4, boop1 & side1 & open1 & kick
B = snare1, ramp, boop1 & side1 & open1 & kick
C = bass2, diarp, boop2 & side2 & open2 & snare2 & kick
F = bass2, lead1(2), boop2 & side2 & open2 & snare2 & kick
G = bass3, lead2 * 2, open3 & snare2 & side3 & kick
H = lead3 & fill, lead2 * 2, bass3
I = boop2 & side2 & open2 & snare2 & kick, lead4 * 2, bass4
J = boop2 & side2 & open2 & snare2 & kick, unit, bass2 * 4
K = boop1 * 4 & side2[:8] & open2[:8] & snare2 & kick, open4, boop3
L = boop2 & side2 & open2 & snare2 & kick, side4 * 2 | lead1(1) | side4 * 2, boop4
sections = A, B, C, F, G, H, I, J, K, L
tonic = B3
speed = 16
scale = naturalminor
