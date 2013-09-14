	pea	script
	move	#32,-(sp)
	trap	#14
	addq.l	#6,sp

	moveq	#49,d7

vsync:	move	#37,-(sp)
	trap	#14
	addq.l	#2,sp

	dbra	d7,vsync

	clr	-(sp)
	trap	#1

script:	dc.b	$7,$ff,$8,$00,$9,$00,$A,$00
	dc.b	$82,1
	dc.b	$8,$0d
	dc.b	$82,1
	dc.b	$8,$00
	dc.b	$8,$0d
	dc.b	$8,$00
	dc.b	$82,2
	dc.b	$8,$0d
	dc.b	$82,2
	dc.b	$80,$10
	dc.b	$81,$8,-1,$0d
	dc.b	$80,$10
	dc.b	$81,$8,-2,$0d
	dc.b	$8,$0f
	dc.b	$82,0
