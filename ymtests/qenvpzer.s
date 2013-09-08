	clr.l	-(sp)
	move.w	#$20,-(sp)	; supervisor mode
	trap	#1
	addq.l	#6,sp
	move.l	d0,super

	move.b	#$07,$ff8800
	move.b	$ff8800,d0	; sic
	ori.b	#$3f,d0		; all off
	move.b	#$07,$ff8800	; required?
	move.b	d0,$ff8802

	move.l	#$08001000,$ff8800	; variable A
	move.l	#$0d000a00,$ff8800	; triangle
	move.l	#$0b000000,$ff8800	; zero fine

	moveq	#9,d0		; tries - 1

loop:	move.l	#$0c000f00,$ff8800	; long env

	move.w	#30000,d3
delay:	dbra	d3,delay

	move.l	#$0c000000,$ff8800	; zero env

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
