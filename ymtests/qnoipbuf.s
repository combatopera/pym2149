	clr.l	-(sp)
	move.w	#$20,-(sp)	; supervisor mode
	trap	#1
	addq.l	#6,sp
	move.l	d0,super

	move.b	#$07,$ff8800
	move.b	$ff8800,d0	; sic
	andi.b	#$c0,d0		; all on
	ori.b	#$37,d0		; noise A
	move.b	#$07,$ff8800	; required?
	move.b	d0,$ff8802

	move.l	#$08000f00,$ff8800	; loud A

	moveq	#9,d0		; tries - 1

loop:	move.l	#$06001f00,$ff8800	; long noise

	move.w	#30000,d3
delay:	dbra	d3,delay

	move.l	#$06000100,$ff8800	; short noise

	move.w	#30000,d3
delay2:	dbra	d3,delay2

	dbra	d0,loop

	move.l	#$08000000,$ff8800	; quiet A

	move.l	super,-(sp)
	move.w	#$20,-(sp)	; user mode
	trap	#1
	addq.l	#6,sp

	clr.w	-(sp)		; exit
	trap	#1

super:	ds.l	1
