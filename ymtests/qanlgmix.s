	clr.l	-(sp)
	move.w	#$20,-(sp)	; supervisor mode
	trap	#1
	addq.l	#6,sp
	move.l	d0,super

	move.b	#$07,$ff8800
	move.b	$ff8800,d0	; sic
	ori.b	#$3f,d0		; all off
	move.b	#$07,$ff8800	; required?
	move.b	d0,$ff8802	; silence

	moveq	#$0f,d0
	moveq	#$0f,d1
	moveq	#$0f,d2

next:	move.b	#$08,$ff8800
	move.b	d0,$ff8802
	move.b	#$09,$ff8800
	move.b	d1,$ff8802
	move.b	#$0a,$ff8800
	move.b	d2,$ff8802

	move.w	#10000,d3
delay:	dbra	d3,delay

	dbra	d0,next
	moveq	#$0f,d0
	dbra	d1,next
	moveq	#$0f,d1
	dbra	d2,next

	move.l	super,-(sp)
	move.w	#$20,-(sp)	; user mode
	trap	#1
	addq.l	#6,sp

	clr.w	-(sp)		; exit
	trap	#1

super:	ds.l	1
