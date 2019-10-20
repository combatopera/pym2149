from .lc import V, D, E, naturalminor, topitch
from .pitches import C4

class Kick:

    level = V('11,13')
    nf = V('1,0')
    tf = V('0,1')
    pitch = V('2x44.01 36 32.01')

    def on(self, frame, chip):
        if frame < 4:
            chip.level = self.level[frame]
            chip.noiseflag = self.nf[frame]
            chip.toneflag = self.tf[frame]
            chip.noiseperiod = 12
            chip.tonepitch = self.pitch[frame]

class Snare:

    level = V('11 14x13//13,0')
    nf = V('1 2x,1')
    tf = V('0 4x1,0')
    np = V('12//6,10') << 1
    pitch = V('.02') + V('57 54 52 51') >> 1

    def on(self, frame, chip):
        chip.level = self.level[frame]
        chip.toneflag = self.tf[frame]
        if self.nf[frame]:
            chip.noiseflag = True
            chip.noiseperiod = self.np[frame]
        chip.tonepitch = self.pitch[frame]

class Hat:

    def on(self, frame, chip):
        if frame < 1:
            chip.level = 10
            chip.noiseflag = True
            chip.toneflag = False
            chip.noiseperiod = 12

class Bass:

    levels = V('13//12,10'), V('13//5,12')
    timbre = D('-,--')
    vib = V('5.5x,/2 5x1/4 -1/2') * V('.145') - V('.01')

    def on(self, frame, chip, degree, velocity, vibshift):
        chip.level = velocity[frame].pick(self.levels)[frame]
        chip.toneflag = True
        chip.tonepitch = topitch((degree + self.timbre)[frame]) + (self.vib << vibshift[frame])[frame]

class Simple:

    def on(self, frame, chip, degree):
        chip.level = self.level[frame]
        chip.toneflag = True
        chip.tonepitch = topitch(degree[frame]) + self.vib[frame]

class Lead(Simple):

    level = V('13 7x12 11//11,0')
    vib = V('6.75x,/1.25 .1/2.5 -.1/1.25')

class Pluck(Simple):

    level = V('13//13,0')
    vib = V('/1.25,.1/2.5 -.1/2.5') << .25

class Arp:

    levels = [V('12//14,5') + V(l) for l in '01']
    chords = D('1 3 5 +').inversions()

    def on(self, frame, chip, degree, inv = V('0'), velocity = V('1')):
        chip.level = velocity[frame].pick(self.levels)[frame]
        chip.toneflag = True
        chip.tonepitch = topitch((degree + inv[frame].pick(self.chords))[frame])

def bass(degree):
    return E(Bass, '1', degree = degree,
            velocity = V('1 2x 3x1 0 2x1 2x 2x1 2x 1'),
            vibshift = V('0 6 7x 6 3x 6 2x'))

drums = E(Kick, '3 2x 2 1', ['3 1'] * 2) & E(Snare, '4/3') >> 2
chords1 = D('1 4 7- 1').of(8)
chords2 = D('1 7-').of(16)
bass1 = bass(chords1 + D('1 2x+ 1 + 1 7 1|1 2x+ 1 3x+ 7-|1 2x+ 1 + 1 2 1|1 2x+ 1 3x+ 5-'))
bass2 = bass(chords2 + D('1 2x+ 1 + 1 5- 1|1 2x+ 1 3x+ 1|1 2x+ 1 + 1 5- 1|1 2x+ 1 3x+ 1'))
arp1 = E(Arp, '1',
        degree = D('8x 8x- 16x') + chords1,
        inv = V('8x 8x2 16x'))
arp2 = E(Arp, '1',
        degree = D('+') + chords2,
        velocity = V('0'))
lead = E(Lead, '2x .5 1 3 3x.5|2x .5 1 3.5 1|2x 3x.5 1 .5 2 2x.5|2x 3x.5 2x 5x.5',
        degree = D('+') + chords1 + D('4x 5- 2x7- 6x 5- 7- 5-|2x 2x7- 1 2x7- 9x5-|5x 5- 7- 7x 2 3|5x 5- 7- 2x 2x+ 5 7 4# 4 3').of(.5))
pluck = E(Pluck, '.5',
        degree = chords2 + D('+ 1 - 2+ 2 - 3+ 3 3- 2+ 2 2- 3+ 3 3- 4+|5+ 5 5- 4+ 4 4- 3+ 3 3- 2+ 2 2- 3+ 3 3- 2+').of(.5))
hat = E(Hat, '.5')
A = arp1, bass1 & drums
B = lead, bass1 & drums, arp1
C = pluck & hat, bass2 & drums, arp2
sections = A, B, B, C, C
tonic = C4 + .04
speed = 14
scale = naturalminor
