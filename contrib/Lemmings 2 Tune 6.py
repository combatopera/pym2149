from . import V, D, E, naturalminor, unit, topitch
from .pitches import B3, C2

class CommonDrum:

    ison = V('4x1,0')
    level = V('2x15,14')

    def _on(self, frame, ym, np):
        if self.ison[frame]:
            ym.level = self.level[frame]
            ym.noiseflag = True
            ym.toneflag = True
            if ym.noisepriority():
                ym.noiseperiod = np
            return True

class Kick(CommonDrum):

    def on(self, frame, ym):
        if super()._on(frame, ym, 21):
            ym.tonepitch = C2 - .11

class Snare(CommonDrum):

    pitch = V('2x60.04 55.06 51.19')

    def on(self, frame, ym):
        if super()._on(frame, ym, 21):
            ym.tonepitch = self.pitch[frame]

class Boop(CommonDrum):

    basedegree = D('++')

    def on(self, frame, ym, degree, attenuation = V('0'), np = V('21')):
        if super()._on(frame, ym, np[frame]):
            ym.level -= attenuation[frame]
            ym.tonedegree = (self.basedegree + degree)[frame]

class Fill(Boop):

    def on(self, frame, ym, degree):
        ym.level = 0
        ym.noiseflag = False
        ym.toneflag = False
        super().on(frame, ym, degree, np = V('1'))

class Side:

    ison = V('8x1,0')
    level = V('6x15//,12')

    def on(self, frame, ym, degree):
        if self.ison[frame]:
            ym.level = self.level[frame]
            ym.noiseflag = True
            ym.toneflag = True
            if ym.noisepriority():
                ym.noiseperiod = 21
            ym.tonedegree = degree[frame]

class Open:

    ison = V('8x1,0')
    level = V('6x15//,12')

    def on(self, frame, ym, attenuation = V('0'), np = V('1')):
        if self.ison[frame]:
            ym.level = self.level[frame] - attenuation[frame]
            ym.noiseflag = True
            ym.toneflag = False
            ym.noiseperiod = np[frame]

class Bass:

    levels = V('6x15// 2x13,0'), V('4x15 4x14,0')
    tf = V('8x1,0')
    basedegree = D('-')

    def on(self, frame, ym, degree, velocity = V('1')):
        ym.level = velocity[frame].pick(self.levels)[frame]
        ym.noiseflag = False
        ym.toneflag = self.tf[frame]
        ym.tonedegree = (self.basedegree + degree)[frame]

class Lead:

    levels = V('4x15 17x14 6x13,12'), V('4x15,14'), V('4x15,14')
    offlevel = V('5x14 24x13//,9')
    vibs = V('0'), V('0'), V('8x 3.5x/,7x.3/ 7x-.3/')

    def _common(self, frame, ym, degree, velocity):
        ym.noiseflag = False
        ym.toneflag = True
        ym.tonepitch = topitch(degree[frame]) + velocity[frame].pick(self.vibs)[frame]

    def on(self, frame, ym, degree, velocity):
        self._common(frame, ym, degree, velocity)
        ym.level = velocity[frame].pick(self.levels)[frame]

    def off(self, frame, ym, degree, velocity, onframes):
        self._common(frame, ym, degree, velocity)
        ym.level = (self.offlevel >> onframes)[frame]

class Tone:

    level = V('15x15//,10')

    def on(self, frame, ym, degree):
        ym.level = self.level[frame]
        ym.noiseflag = False
        ym.toneflag = True
        ym.tonedegree = degree[frame]

class Ping:

    levels = V('16x12//,8'), V('16x14//,10')

    def on(self, frame, ym, degree, velocity):
        ym.level = velocity[frame].pick(self.levels)[frame]
        ym.noiseflag = False
        ym.toneflag = True
        ym.tonedegree = degree[frame]

class Diarp:

    whichdegree = V('2 1').of(4)

    def on(self, frame, ym, degree1, degree2, level):
        ym.level = level[frame]
        ym.noiseflag = False
        ym.toneflag = True
        ym.tonedegree = self.whichdegree[frame].pick({1: degree1, 2: degree2})[frame]

class Ramp:

    level = V('4x15,14')
    tp = (V('4x-4/ 4x/') * V('128x/ 64')) >> .5

    def on(self, frame, ym, degree):
        ym.level = self.level[frame]
        ym.noiseflag = False
        ym.toneflag = True
        ym.tonepitch = topitch(degree[frame]) + .06
        ym.toneperiod += self.tp[frame]

def lead1(firstslide, lastoff):
    return E(Lead, '3x2 2x|4x 2 2x', ['2 1.5 .5 4x'] * 2, "3x2 2x|4x 4/%s" % lastoff,
            degree = D("2x3 2x2 3x 2|3 5/%s 2 3 2x 3 4|3.5x5 .5x6 5 4/.5 2 3|3.5x4 .5x5 4 3/.5 1 2|2x3 2x2 3x 2|3 5/.25 2 3 4x" % firstslide),
            velocity = V('18x 1.5x1 6.5x 1.5x1 4.5x|12x 4x1'))

snare1 = E(Snare, '.5 1 .5 1 .5 1 2x.25 6x.5')
snare2 = E(Snare, '8') >> 3.5
bass1 = E(Bass, '4x1.5 2x',
        degree = D('7x- 7--'),
        velocity = V('0'))
bass2 = E(Bass, '1 2x.5 2x',
        degree = D('1 ++ 5- 7|1 .5x++ .5x+ 5- 7'))
bass3 = bass2 | E(Bass, '1 2x.5 2x',
        degree = D('6- 6 3- 3|6- 6 3- 3|4- 4 1 4|4- 4 1 4|7- 7 4 7|7- 7 4 7'))
bass4 = bass2 | E(Bass, '1 2x.5 2x',
        degree = D('6- 6 3- 3|6- 6 3- 6|1 ++ 5- 7|1 .5x++ .5x+ 5- 7|7- 7 4 7|7- 7 4 7'))
ramp = E(Ramp, '8',
        degree = D('4'))
diarp = E(Diarp, '8x4',
        degree1 = D('+'),
        degree2 = D('4x3+ 4x2+'),
        level = V('16x15 12x14// 4x11'))
boop1 = E(Boop, '3.5/ 2x2 .5',
        degree = D('3'))
boop2 = E(Boop, '11.5/ 1 2x.5 1 3x.5',
        degree = D('26x3 5 3x3 5 3').of(.5))
boop3 = E(Boop, '.5',
        degree = D('3 5').of(.5),
        attenuation = V('3 4').of(.5))
boop4 = E(Boop, '.5',
        degree = D('3 5').of(.5),
        attenuation = V('4 5').of(.5))
kick = E(Kick, '2')
side1 = E(Side, '/ 2x.5 6/',
        degree = D('1'))
side2 = E(Side, '/ 2x.5 3/ 2x.5 2/|/ 2x.5 6/',
        degree = D('7- 4x 3x7-'))
side3 = E(Side, '/ 2x.5 2/',
        degree = D('1'))
side4 = E(Side, '2x .5 1 .5 2x .5 1 .5 2x .5 1 .5 8x.5',
        degree = D('++') + D('4x 7- 2x 7- 4x 7- 2x 7- 4x 7- 2x 7- 3 2 1 7- 3 2 1 7-').of(.5))
open1 = E(Open, '.5/ 2 .5 2x2 1')
open2 = E(Open, '.5/ 2.5 4 2x.5|.5/ 2.5 5')
open3 = E(Open, '.5/ 2 .5 1.5 2 3x.5')
open4 = E(Open, '.5',
        attenuation = V('1 3 2 1 3 2 1 3 2 1 3 2 1 3 2 4').of(.5),
        np = V('2x1 4x21 1 7x21 2x1').of(.5))
lead2 = E(Tone, ['2/1 1 4x.5 3x'] * 3, '2x2/1 4x',
        degree = D('-') + D('2x 1.5x3 .5x2 .5x3 .5x2 3 1 7-|2x6- 1.5x .5x7- .5x .5x7- 1 6- 5-|2x4- 1.5x6#- .5x6- .5x6#- .5x6- 6#- 4- 6#-|2x7- 2x 2 7- 1 2'))
lead3 = E(Lead, '6', ['1 3'] * 4, '2|4 4/',
        degree = D('+') + D('6x/.5 3 3x2 3 3x/.5 3 3x2 3 3x4 2x|8x2'),
        velocity = V('2'))
lead4 = E(Ping, ['2/1 1 4x.5 3x'] * 3, '2/1 6/5',
        degree = D('++') + D('2x 1.5x3 .5x2 .5x3 .5x2 3 1 7-|2x6- 1.5x3 .5x2 .5x3 .5x2 3 1 7-|2x 1.5x3 .5x2 .5x3 .5x2 2x3 1|8x2'),
        velocity = V('26x1 6x'))
fill = E(Fill, '28/ 8x.5',
        degree = D('3 2').of(.5))
A = snare1, bass1 * 4, boop1 & side1 & open1 & kick
B = snare1, ramp, boop1 & side1 & open1 & kick
C = bass2, diarp, boop2 & side2 & open2 & snare2 & kick
F = bass2, lead1(0, 2), boop2 & side2 & open2 & snare2 & kick
G = bass3, lead2 * 2, open3 & snare2 & side3 & kick
H = lead3 & fill, lead2 * 2, bass3
I = boop2 & side2 & open2 & snare2 & kick, lead4 * 2, bass4
J = boop2 & side2 & open2 & snare2 & kick, unit, bass2 * 4
K = boop1 * 4 & side2[:8] & open2[:8] & snare2 & kick, open4, boop3
L = boop2 & side2 & open2 & snare2 & kick, side4 * 2 | lead1(.25, 1) | side4 * 2, boop4
sections = A, B, C, F, G, H, I, J, K, L
tonic = B3
speed = 16
scale = naturalminor
