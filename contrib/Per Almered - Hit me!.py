from pym2149.lc import V, D, E, major
from pym2149.pitches import F4

class Bass:

    envshape = 0x0a
    envpitch = D('2x++,+')

    def on(self, frame, chip, degree, hard = V('0')):
        chip.fixedlevel = 15
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch(degree[frame])
        chip.envflag = True
        if frame < 1 and hard[frame]:
            chip.envshape = self.envshape
        chip.envperiod = chip.toenvperiod(chip.topitch((self.envpitch + degree)[frame]))

class Kick:

    level = V('13 3x15 13//3 10')
    nf = V('1,0')
    tf = V('0,1')
    pitch = V('2x47 43 40 32 3x24')

    def on(self, frame, chip):
        if frame < 8:
            chip.fixedlevel = self.level[frame]
            chip.noiseflag = self.nf[frame]
            chip.toneflag = self.tf[frame]
            chip.noiseperiod = 7
            chip.tonepitch = self.pitch[frame]

class Arp:

    level = V('14//15 18x9 8 2x7 6//24,0')
    chords = D('1 3 5').inversions()
    vib = V('15.5x,/3 -.4/6 .4/3')

    def on(self, frame, chip, degree, inv = V('0')):
        chip.fixedlevel = self.level[frame]
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch((degree + inv[frame].pick(self.chords))[frame]) + self.vib[frame]

bass = E(Bass, '1/.5 1/.5 .5 1/.5 1/.5 .5 1/.5 .5 1.5/1',
        degree = D('--') + D('2- 2 .5x 2 1.5x2- 2 .5x 1.5x2'),
        hard = V('1,0'))
kick = E(Kick, '2')
arp = E(Arp, '1.5 6.5',
        degree = D('1.5x 6.5x4'),
        inv = V('1.5x2 6.5x1'))
A = bass, kick, arp
sections = A,
scale = major
tonic = F4
speed = 20
