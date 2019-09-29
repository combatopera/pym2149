from pym2149.lc import V, D, E, major
from pym2149.pitches import F4

class Arp:

    level = V('14//15 18x9 8 2x7 6//24,0')
    chords = D('1 3 5').inversions()
    vib = V('15.5x,0/3 -.4/6 .4/3')

    def on(self, frame, chip, degree, inv = V('0')):
        chip.fixedlevel = self.level[frame]
        chip.noiseflag = False
        chip.toneflag = True
        chip.tonepitch = chip.topitch((degree + inv[frame].pick(self.chords))[frame]) + self.vib[frame]

arp = E(Arp, '1.5 6.5',
        degree = D('1.5x 6.5x4'),
        inv = V('1.5x2 6.5x1'))
A = arp, arp, arp
sections = A,
scale = major
tonic = F4
speed = 20
