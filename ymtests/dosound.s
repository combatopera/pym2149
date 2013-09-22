	bsr	tick
	lea	scripts,a6

next:	move.l	(a6)+,-(sp)
	move	#32,-(sp)
	trap	#14
	addq.l	#6,sp

	moveq	#49,d7
sleep:	bsr	tick
	dbra	d7,sleep

	tst.l	(a6)
	bne	next

	clr	-(sp)
	trap	#1

tick:	move	#37,-(sp)
	trap	#14
	addq.l	#2,sp
	rts

script:	dc.b	$7,$ff,$8,$00,$9,$00,$A,$00
	dc.b	$82,1
	dc.b	$8,$0d
	dc.b	$82,1
	dc.b	$8,$00
	dc.b	$8,$0f
	dc.b	$8,$00
	dc.b	$82,2
	dc.b	$8,$0d
	dc.b	$82,2
	dc.b	$80,$10
	dc.b	$81,$8,-1,$0d
	dc.b	$80,$10
	dc.b	$81,$8,-2,$0d

script2:	dc.b	$7,$ff,$8,$00,$9,$00,$A,$00
	dc.b	$80,$ff
	dc.b	$81,$8,1,$0d
	dc.b	$80,$fe
	dc.b	$81,$8,2,$0d

scripts:	dc.l	script,script2,0
