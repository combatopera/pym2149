	pea	clear
	move	#$09,-(sp)	; Cconws.
	trap	#1
	addq.l	#6,sp

	move.l	4(sp),a6		; Basepage.
	pea	$81(a6)		; Command line, skipping length byte.
	move	#$09,-(sp)	; Cconws.
	trap	#1
	addq.l	#6,sp

	pea	crlf
	move	#$09,-(sp)	; Cconws.
	trap	#1
	addq.l	#6,sp

	clr	-(sp)		; For reading.
	pea	$81(a6)		; Command line as above.
	move	#$3d,-(sp)	; Fopen.
	trap	#1
	addq.l	#8,sp

	tst.l	d0		; Recommended to test whole thing.
	blt	error
	move	d0,d7		; Handle.

	lea	ticks,a5
read:	pea	(a5)		; Current position in buffer.
	move.l	#$1000,-(sp)	; Max bytes to read this time.
	move	d7,-(sp)		; Handle.
	move	#$3f,-(sp)	; Fread.
	trap	#1
	lea	12(sp),sp

	tst.l	d0
	beq	play		; EOF.
	blt	error		; Don't add error to buffer position!
	add.l	d0,a5		; Adjust buffer position.
	bsr	print
	bra	read

play:	pea	ticks+2		; The actual data.
	move	#32,-(sp)		; Dosound.
	trap	#14
	addq.l	#6,sp

	bsr	vsync		; Sound probably starts now.
	clr.b	crlf+1		; Hack to stay on same line.
	moveq	#0,d7		; Clear high word for printing.
	move	ticks,d7		; There are this many ticks left.
loop:	move.l	d7,d0
	bsr	print
	bsr	vsync
	dbra	d7,loop

anykey:	move	#$08,-(sp)	; Cnecin.
	trap	#1
	addq.l	#2,sp

	clr	-(sp)		; Pterm0.
	trap	#1

error:	bsr	print
	bra	anykey

print:	lea	digits,a0
	lea	crlf,a1
	moveq	#7,d2		; There are 8 digits.
print0:	move	d0,d1
	and	#$0f,d1
	move.b	0(a0,d1.w),-(a1)
	lsr.l	#4,d0
	dbra	d2,print0

	pea	(a1)
	move	#$09,-(sp)	; Cconws.
	trap	#1
	addq.l	#6,sp
	rts

vsync:	move	#37,-(sp)		; Vsync.
	trap	#14
	addq.l	#2,sp
	rts

	.data

digits:	dc.b	'0123456789abcdef'
clear:	dc.b	$1b,'E',0
number:	dc.b	'xxxxxxxx'
crlf:	dc.b	13,10,0
	even

	.bss

ticks:	ds.w	1
