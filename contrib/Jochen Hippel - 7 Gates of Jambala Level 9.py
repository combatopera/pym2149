from lurlene import V, D, E, naturalminor
from lurlene.pitch import C4

class Kick:

    ison = V('4x1,0')
    level = V('11,13')
    nf = V('1,0')
    tf = V('0,1')
    pitch = V('2x44.01 36 32.01')

    def on(self, frame, ym):
        if self.ison[frame]:
            ym.level = self.level[frame]
            ym.noiseflag = self.nf[frame]
            ym.toneflag = self.tf[frame]
            ym.noiseperiod = 12
            ym.tonepitch = self.pitch[frame]

class Snare:

    level = V('11 14x13//13,0')
    nf = V('1 2x,1')
    tf = V('0 4x1,0')
    np = V('6x12//,10') << 1
    pitch = V('.02') + V('57 54 52 51') >> 1

    def on(self, frame, ym):
        ym.level = self.level[frame]
        ym.toneflag = self.tf[frame]
        if self.nf[frame]:
            ym.noiseflag = True
            ym.noiseperiod = self.np[frame]
        ym.tonepitch = self.pitch[frame]

class Hat:

    ison = V('1,0')

    def on(self, frame, ym):
        if self.ison[frame]:
            ym.level = 10
            ym.noiseflag = True
            ym.toneflag = False
            ym.noiseperiod = 12

class Bass:

    levels = V('5x13//,12'), V('12x13//,10')
    timbre = D('-,--')
    vib = V('5.5x,2x/ 5x1/4 2x-1/') * V('.145') - V('.01')

    def on(self, frame, ym, degree, att, vibshift):
        ym.level = att[frame].pick(self.levels)[frame]
        ym.toneflag = True
        ym.tonedegree = (degree + self.timbre)[frame]
        ym.tonepitch += (self.vib << vibshift[frame])[frame]

class Simple:

    def on(self, frame, ym, degree):
        ym.level = self.level[frame]
        ym.toneflag = True
        ym.tonedegree = (self.degree + degree)[frame]
        ym.tonepitch += self.vib[frame]

class Lead(Simple):

    level = V('13 7x12 11x11//,0')
    vib = V('6.75x,1.25x/ 2.5x.1/ 1.25x-.1/')
    degree = D('+')

class Pluck(Simple):

    level = V('13x13//,0')
    vib = V('1.25x/,2.5x.1/ 2.5x-.1/') << .25
    degree = D('1')

class Arp:

    levels = [V('14x13//,6') - V(l) for l in '01']
    chords = D('1 3 5 +').inversions()

    def on(self, frame, ym, degree, inv = V('0'), att = V('0')):
        ym.level = att[frame].pick(self.levels)[frame]
        ym.toneflag = True
        ym.tonedegree = (degree + inv[frame].pick(self.chords))[frame]

def bass(degree):
    return E(Bass, '1', degree = degree,
            att = V('0 2x1 3x 1 2x 2x1 2x 2x1 0'),
            vibshift = V('0 6 7x 6 3x 6 2x'))

drum1 = E(Kick, '3 2x 2 1', ['3 1'] * 2) & E(Snare, '1 3z') >> 2
prog1 = D('1 4 7- 1').of(8)
prog2 = D('1 7-').of(16)
bass1 = bass(prog1 + D('1 2x+ 1 + 1 7 1|1 2x+ 1 3x+ 7-|1 2x+ 1 + 1 2 1|1 2x+ 1 3x+ 5-'))
bass2 = bass(prog2 + D('1 2x+ 1 + 1 5- 1|1 2x+ 1 3x+ 1|1 2x+ 1 + 1 5- 1|1 2x+ 1 3x+ 1'))
arps1 = E(Arp, '1',
        degree = D('8x 8x- 16x') + prog1,
        inv = V('8x 8x2 16x'))
arps2 = E(Arp, '1',
        degree = D('+') + prog2,
        att = V('1'))
vers1 = E(Lead, '2x .5 1 3 3x.5|2x .5 1 3.5 1|2x 3x.5 1 .5 2 2x.5|2x 3x.5 2x 5x.5',
        degree = prog1 + D('4x 5- 2x7- 6x 5- 7- 5-|2x 2x7- 1 2x7- 9x5-|5x 5- 7- 7x 2 3|5x 5- 7- 2x 2x+ 5 7 4# 4 3').of(.5))
brdg1 = E(Pluck, '.5',
        degree = prog2 + (D(['+ 1 -'] * 5, '+') + D('3x 2x2 1 3x3 3x2 3x3 4|3x5 3x4 3x3 3x2 3x3 2')).of(.5))
hiha1 = E(Hat, '.5')
Intr1 = arps1, bass1 & drum1
VERS1 = vers1, bass1 & drum1, arps1
BRDG1 = brdg1 & hiha1, bass2 & drum1, arps2
sections = (
    Intr1,
    VERS1, VERS1,
    BRDG1, BRDG1,
)
tonic = C4 + .04
speed = 14
scale = naturalminor
