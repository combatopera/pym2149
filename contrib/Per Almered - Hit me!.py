from pym2149.lc import V, D, E, major
from pym2149.pitches import F4

class Bass:

    envshape = 0x0a
    envpitches = D('2x++,+'), D('2x++ 5x+,1'), D('+')

    def on(self, frame, chip, degree, slap = V('0'), hard = V('0')):
        chip.fixedlevel = 15
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[frame])
        chip.envflag = True
        if frame < 1 and hard[frame]:
            chip.envshape = self.envshape
        chip.envpitch = chip.topitch((slap[frame].pick(self.envpitches) + degree)[frame])

class Kick:

    level = V('13 3x15 13//3 10')
    nf = V('1,0')
    tf = V('0,1')
    pitch = V('2x47 43 40 32 3x24')

    def on(self, frame, chip, att = V('0'), np = V('7')):
        if frame < 8:
            chip.fixedlevel = self.level[frame] - att[frame]
            chip.noiseflag = self.nf[frame]
            chip.toneflag = self.tf[frame]
            chip.noiseperiod = np[frame]
            chip.tonepitch = self.pitch[frame]

class Snare:

    level = V('4x15 13 11'), V('4x14,12'), V('4x13 11 10')
    nf = V('1 3x,1')
    np = V('17,13')
    tf = V('4x1,0')
    pitch = V('64 60 57 55')

    def on(self, frame, chip, att = V('0')):
        if frame < 6:
            chip.fixedlevel = att[frame].pick(self.level)[frame]
            chip.noiseflag = self.nf[frame]
            if chip.noisepriority():
                chip.noiseperiod = self.np[frame]
            chip.toneflag = self.tf[frame]
            chip.tonepitch = self.pitch[frame]
            return True

class Snare2(Snare):

    np2 = V('17,1'), Snare.np

    def on(self, frame, chip, att):
        if super().on(frame, chip, att) and chip.noisepriority():
            chip.noiseperiod = att[frame].pick(self.np2)[frame]

class Arp:

    levels = V('10'), V('14//15 18x9 8 2x7 6//24,0')
    chords = D('1 3 5').inversions()
    vib = V('15.5x,/3 -.4/6 .4/3')

    def on(self, frame, chip, degree, inv = V('0'), vel = V('1')):
        chip.fixedlevel = vel[frame].pick(self.levels)[frame]
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch((degree + inv[frame].pick(self.chords))[frame]) + self.vib[frame]

class Arp2:

    level = V('2x13 3x12 2x11 6x10,9')

    def on(self, frame, chip, degree1, degree2, degree3):
        chip.fixedlevel = self.level[frame]
        chip.toneflag = True
        chip.tonepitch = chip.topitch([degree1, degree2, degree3][int(frame) % 3][frame])

class Lead:

    hilevel = V('3x15 14 2x13,12')
    lolevel = V('3x11 3x10,9')
    levels = hilevel, hilevel - V('1'), hilevel - V('2'), V('3x12 11,10'), lolevel, lolevel - V('1'), lolevel - V('2'), lolevel - V('3')
    vib = V('40.5x,/3 -.4/6 .4/3')

    def on(self, frame, chip, degree, att = V('0'), vibshift = V('0')):
        chip.fixedlevel = att[frame].pick(self.levels)[frame]
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[frame]) + (self.vib << vibshift[frame])[frame]

class Bright:

    level = V('13 14//4,10')
    arp = D(['++ + 1'] * 2, '+,1')

    def on(self, frame, chip, degree):
        chip.fixedlevel = self.level[frame]
        chip.toneflag = True
        chip.tonepitch = chip.topitch((degree + self.arp)[frame])

class Luke:

    level = V('12 13 14 12,9'), V('11 12 13 11 9 6 4 2x3 2 1,0'), V('10 11 12 10,8'), V('2x10 11 10 7'), V('2x9 10 9,7'), V('2x8 9 8,6'), V('2x7 8 7,5'), V('6 2x7 6,5'), V('5 2x6 5,4'), V('4 2x5 4,3'), V('3 4x4//4 2,1')
    arp = D('1 +')

    def on(self, frame, chip, degree, att = V('1')):
        chip.fixedlevel = att[frame].pick(self.level)[frame]
        chip.toneflag = True
        chip.tonepitch = chip.topitch((degree + self.arp)[frame])

bass1 = E(Bass, 2 * ['/.5 /.5 .5 /.5 /.5 .5 /.5 .5 1.5/1|/.5 /.5 .5 /.5 /.5 .5 /.5 4x.5'],
        degree = D('--') + D('2- 2 .5x 2 1.5x2- 2 .5x 1.5x2|2- 2 .5x 2 1.5x2- 2 .5x .5x2 .5x6- .5x'),
        hard = V('1,0'))
bass2 = E(Bass, '/.5 /.5 .5 /.5 /.5 .5 /.5 4x.5|/.5 /.5 .5 /.5 9x.5',
        degree = D('---') + D('2 2+ .5x+ 2+ 1.5x2 2+ .5x+ .5x2+ .5x5- .5x5|6- 6 .5x5 6 6- .5x6 .5x7- .5x7 .5x .5x+ .5x# .5x#+'))
bass3 = E(Bass, '32x.5',
        degree = D('---') + D(['2 2+'] * 5, '3 3+ 4 4+ 5- 5', ['6- 6'] * 5, '7- 7 1 + # #+').of(.5),
        slap = V(['0 1'] * 7, '2x').of(.5))
bass3a = E(Bass, ['.75/ .25'] * 7, '/',
        degree = D('---') + D('5x2 3 2x4|5x6- 7- 2x'))
bass6 = E(Bass, '56x.5',
        degree = D('---') + D(['1 +'] * 4, '2 2+ 2 2+ 2 2+ 1 +', ['7- 7'] * 4, '1 + 1 + 5- 5 5#- 5#', '6- 6 6- 6 6- 6 1 +|2 2+ 2 2+ 7- 7 2 2+|2x3 3+ 3 2+ 3+ 7 2+').of(.5))
bass7 = E(Bass, '.75/.25 3x/.25 .5',
        degree = D('2'),
        slap = V('2'))
kick1 = E(Kick, '2')
kick1a = E(Kick, '2',
        np = V('1,7'))
kick2 = E(Kick, '12x .5/ .25 .75 2.5')
kick7 = E(Kick, '.5 .25 .5 .25 2x.5 .25 .5 .75',
        att = V('.5x 1.5x1 .5x .75x1 .75x'))
snare2 = E(Snare, '13/ 1 .25 .5 .25 .5 2x.25',
        att = V('14.25x .75x2 .5x .25x2 .25x'))
snare3 = E(Snare, '/ 3x2 .75 1.25/1 2x2 1.25 .75 .5 2x.25')
snare6 = E(Snare, '/ 7x2 .75 .25')
snare7 = E(Snare2, '.25/ 2x.75 .5 .75 .5 2x.25',
        att = V('3.5x .25x1 .25x'))
arp1 = E(Arp, '1.5 6.5',
        degree = D('1.5x 6.5x4 1.5x5 6.5x'),
        inv = V('1.5x2 6.5x1 1.5x 6.5x2'))
arp4 = E(Arp, '.25/ /.5 .25 .75/.5 7x/.5 .25 .75/.5 3x/.5 1.25/.75 2x.75/.5',
        degree = D('1.5x 6.5x4 1.5x5 6.5x'),
        inv = V('1.5x2 6.5x1 1.5x 6.5x2'),
        vel = V('0'))
arp6 = E(Arp2, ['.5/ .5'] * 27, '.5/ .75 3.75/',
        degree1 = D('4x 8x6- 4x|5x 7- 2x6- 2x7- 6x6-'),
        degree2 = D('12x2 4x3|5x3 11x2'),
        degree3 = D('6x5 6x4# 4x5|7x5 4# 3x5 5x4#'))
lead4 = E(Lead, '2x.75 5/.25 3x.5|2x.75 4.5 2x|1.5 3 .5 4x.25 .5 .25 3x.5 .25 2x.5 .25 .5 .25 .5 .25 .5 .25 .5 .25 .5 .25 .5 .25 .5 .25 1',
        degree = D('.75x2 .75x6 .5x+/.5 5x2+ .5x+ 2+/.5 .25x3+ .75x+ 4.5x6 + 6|2x+/.5 3x2+ .25x+ .25x6 .25x5 .25x4 .5x5 .25x4 .5x5 .5x6 .5x4 1.25x2 .25x .5x2 .25x# .5x2# .25x2 .5x3 .25x2# .5x4 .25x3 .5x4# .25x4 .5x5 .25x4# .5x5# .25x5 6'),
        att = V('16x|10.25x .75x1 .75x2 .75x3 .75x4 .75x5 .75x6 1.25x7'))
lead5 = E(Bright, '3.75/ .5 .25 .5 .25 3x.5 .25 2x.5|3.75/ .5 .25 .5 .25 .5 .25 .5 .25 .5 3x.25',
        degree = D('4.25x2+ .25x6 .5x+ .25x5 .5x6 .5x4 .5x5 .25x6 .5x5 .5x2|4.5x2+ .5x+ .25x6 .5x5 .25x4 .5x5 .25x6 .5x5 .25x4 .25x2 .25x'))
lead6 = E(Luke, ['.25 2x.5 .25 3x.5 2x.25 .5|.25 2x.5 .25 %s 2x.5 .25 .75|.25 2x.5 .25 3x.5 2x.25 .5|.25 2x.5 3x.25 2x.5 .25 .5 .25' % x for x in ['.5', '2x.25']],
        degree = D(['1.25x5 .25x2 .5x3 1.25x5 .25x3 .5x2|1.25x5 .25x2 %s 1.25x5 .75x6|1.25x5 .25x2 .5x3 1.25x5 .25x3 .5x2|1.25x5 .25x2 .25x3 .25x5 .5x6# .5x6 .25x5 .5x6 .25x5' % x for x in ['.5x3', '.25x3 .25x2']]))[:-4]
lead8 = E(Luke, ['64x.25'],
        att = V('30x//30 2x10').of(.25),
        degree = D(['2+ 6+ 2++'] * 10, '2+ 6+', ['+ 5+ ++'] * 10, '+ ++').of(.25))
lead9 = E(Lead, ['2x.75 1 3x.5'] * 2, '1.5 6.5',
        degree = D('.35x4b/.35 .4x4 .75x3 6- .35x4b/.35 .15x4 .5x3 .5x6- .35x4b/.35 .4x4 .75x3 6- .35x4b/.35 .15x4 .5x3 .5x4 .75x4/.75 .75x5 6.5x6'),
        vibshift = V('9.5x 6.5x34'))
luke9 = E(Luke, '12/ 16x.25',
        degree = D('4+ 3+ + 6 3+ + 6 4 + 6 4 3 6 4 3 1').of(.25),
        att = V('15x//15 3').of(.25))
A = bass1, kick1, arp1
B = bass2, kick2 & snare2, arp1
C = bass3 * 2, kick1 & snare3 & bass3a, arp1
F = bass3, kick1 & snare3 & bass3a & arp4, lead4
G = bass3, kick1 & snare3 & bass3a, arp1 & lead5 * 2
H = bass6, kick1 & arp6[:-4] & snare6, lead6
I = kick7, arp6[28:] & snare7, bass7[:-.25]
J = bass3, kick1a & snare3 & bass3a, bass7[4:] | lead8[:31.75]
K = bass3, kick1 & snare3 & bass3a & arp4, lead9 & luke9
sections = A, B, C, F, G, G, H, I, J, G, F, K
scale = major
tonic = F4
speed = 20
