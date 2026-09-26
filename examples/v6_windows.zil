"v6_windows.zil - the version-6 screen model (§8.8) in character graphics.

Version 6 was Infocom's graphical Z-machine: eight windows lying on top
of each other, positioned and sized in PIXELS. zforge runs it on a
character terminal by making one unit one character, so this program
draws with box-drawing characters instead of pictures.

What it shows, in order:

  window 1   the status bar, tiled by SPLIT as in version 5 (§8.8.4.1)
  window 2   a panel with a border, moved and resized while it is on
             screen (WINPOS, WINSIZE), with its own colours and cursor
  window 0   the main text, with MARGIN set so the text flows beside
             the panel (§8.8.3.2.1), and scrolling shown by SCROLL

Build and play it with:

    python -m zforge compile examples/v6_windows.zil -o build/v6.z6
    python -m zforge run build/v6.z6 --ui curses"

<VERSION 6>

<CONSTANT PANEL-WINDOW 2>
<CONSTANT PANEL-TOP 3>
<CONSTANT PANEL-LEFT 46>
<CONSTANT PANEL-HEIGHT 9>
<CONSTANT PANEL-WIDTH 32>

<GLOBAL TURNS 0>

<ROUTINE GO ()
	<SPLIT 1>                       ;"§8.8.4.1: tile windows 0 and 1"
	<STATUS-LINE>
	<MAKE-PANEL>
	<SCREEN 0>
	;"§8.8.3.2.1: a right margin that keeps the text clear of the panel"
	<MARGIN 0 <+ <- 80 ,PANEL-LEFT> 2> 0>
	<PUTB ,INPUT-BUFFER 0 78>       ;"§15 read: byte 0 = room for 78 characters"
	<PUTB ,INPUT-BUFFER 1 0>
	<PUTB ,LEX-BUFFER 0 12>         ;"§13.6.3: room for 12 words"
	<PRINTI "The version-6 screen model
">
	<CRLF>
	<PRINTI "There are eight windows (section 8.8.3). This is window 0. To the right, window 2 has a border, its own cursor and its own colours; it was placed with WINPOS and sized with WINSIZE. The right margin of this window keeps the running text clear of it.">
	<CRLF>
	<CRLF>
	<PRINTI "Type MOVE, SCROLL, WRAP or QUIT.">
	<CRLF>
	<MAIN-LOOP>>

<ROUTINE STATUS-LINE ()
	<SCREEN 1>
	<HLIGHT 1>                      ;"reverse video, so the bar stands out"
	<CURSET 1 1 1>
	<PRINTI " zforge v6 demo">
	<CURSET 1 60 1>
	<PRINTI "turns: ">
	<PRINTN ,TURNS>
	<HLIGHT 0>
	<SCREEN 0>>

<ROUTINE MAKE-PANEL ()
	<WINPOS ,PANEL-WINDOW ,PANEL-TOP ,PANEL-LEFT>
	<WINSIZE ,PANEL-WINDOW ,PANEL-HEIGHT ,PANEL-WIDTH>
	<WINATTR ,PANEL-WINDOW 8 0>     ;"buffering only: no wrap, no scroll"
	<DRAW-PANEL>>

<ROUTINE DRAW-PANEL ("AUX" (ROW 2))
	<SCREEN ,PANEL-WINDOW>
	<CLEAR ,PANEL-WINDOW>
	<CURSET 1 1 ,PANEL-WINDOW>
	<BORDER-LINE 1>
	<REPEAT ()
		<COND (<G? .ROW <- ,PANEL-HEIGHT 1>> <RETURN>)>
		<CURSET .ROW 1 ,PANEL-WINDOW>
		<PRINTI "\|">              ;"a bare | is ZIL's line break; \| is the character"
		<CURSET .ROW ,PANEL-WIDTH ,PANEL-WINDOW>
		<PRINTI "\|">
		<SET ROW <+ .ROW 1>>>
	<CURSET ,PANEL-HEIGHT 1 ,PANEL-WINDOW>
	<BORDER-LINE 0>
	<CURSET 2 3 ,PANEL-WINDOW>
	<PRINTI "window 2">
	<CURSET 3 3 ,PANEL-WINDOW>
	<PRINTI "at (">
	<PRINTN <WINGET ,PANEL-WINDOW 0>>
	<PRINTI ",">
	<PRINTN <WINGET ,PANEL-WINDOW 1>>
	<PRINTI ") size ">
	<PRINTN <WINGET ,PANEL-WINDOW 2>>
	<PRINTI "x">
	<PRINTN <WINGET ,PANEL-WINDOW 3>>
	<CURSET 5 3 ,PANEL-WINDOW>
	<PRINTI "attributes: ">
	<PRINTN <WINGET ,PANEL-WINDOW 14>>
	<CURSET 6 3 ,PANEL-WINDOW>
	<PRINTI "font size: ">
	<PRINTN <WINGET ,PANEL-WINDOW 13>>
	<SCREEN 0>>

<ROUTINE BORDER-LINE (TOP "AUX" (COLUMN 2))
	<PRINTI "+">
	<REPEAT ()
		<COND (<G? .COLUMN <- ,PANEL-WIDTH 1>> <RETURN>)>
		<PRINTI "-">
		<SET COLUMN <+ .COLUMN 1>>>
	<PRINTI "+">>

<ROUTINE MAIN-LOOP ("AUX" WORD)
	<REPEAT ()
		<CRLF>
		<PRINTI "> ">
		<PUTB ,INPUT-BUFFER 1 0>         ;"§15 read: byte 1 counts letters ALREADY typed"
		<READ ,INPUT-BUFFER ,LEX-BUFFER>
		<SETG TURNS <+ ,TURNS 1>>
		<STATUS-LINE>
		<SET WORD <GET ,LEX-BUFFER 1>>
		<COND (<EQUAL? .WORD ,W?MOVE> <MOVE-PANEL>)
		      (<EQUAL? .WORD ,W?SCROLL> <SCROLL-TEXT>)
		      (<EQUAL? .WORD ,W?WRAP> <TOGGLE-WRAP>)
		      (<EQUAL? .WORD ,W?QUIT> <QUIT>)
		      (T <PRINTI "MOVE, SCROLL, WRAP or QUIT.">
			 <CRLF>)>>>

<ROUTINE MOVE-PANEL ()
	<CLEAR ,PANEL-WINDOW>            ;"§8.8.5.3: erase where it is now"
	<WINPOS ,PANEL-WINDOW <+ <WINGET ,PANEL-WINDOW 0> 1> ,PANEL-LEFT>
	<DRAW-PANEL>
	<PRINTI "The panel moved down one line: what was already printed stays
where it was (section 8.8.3), so window 2 was erased first.">
	<CRLF>>

<ROUTINE SCROLL-TEXT ()
	<SCROLL 0 1>                     ;"§8.8.3.6: any window, at any time"
	<PRINTI "Window 0 scrolled up one line.">
	<CRLF>>

<ROUTINE TOGGLE-WRAP ()
	<WINATTR 0 1 3>                  ;"operation 3: flip the wrapping bit"
	<PRINTI "Wrapping is now ">
	<COND (<BAND <WINGET 0 14> 1> <PRINTI "on">)
	      (T <PRINTI "off">)>
	<PRINTI ". This sentence is long enough to show what that does to text which reaches the right margin of the window.">
	<CRLF>>

<OBJECT ROOMS>

<GLOBAL INPUT-BUFFER <ITABLE 80 (BYTE)>>
<GLOBAL LEX-BUFFER <ITABLE 50 (BYTE)>>    ;"2 + 4 bytes x 12 words (§13.6.3)"

<SYNTAX MOVE = V-NOOP>
<SYNTAX SCROLL = V-NOOP>
<SYNTAX WRAP = V-NOOP>
<SYNTAX QUIT = V-NOOP>

<ROUTINE V-NOOP () <RTRUE>>
