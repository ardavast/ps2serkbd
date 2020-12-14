#include <ps2serkbd.h>

const char *scancodes[34] {
	PS2SERKBD_MAKE_LEFTSHIFT, PS2SERKBD_MAKE_H, PS2SERKBD_BREAK_H, PS2SERKBD_BREAK_LEFTSHIFT, // H 
	PS2SERKBD_MAKE_E, PS2SERKBD_BREAK_E,                                                      // e 
	PS2SERKBD_MAKE_L, PS2SERKBD_BREAK_L,                                                      // l 
	PS2SERKBD_MAKE_L, PS2SERKBD_BREAK_L,                                                      // l 
	PS2SERKBD_MAKE_O, PS2SERKBD_BREAK_O,                                                      // o 
	PS2SERKBD_MAKE_COMMA, PS2SERKBD_BREAK_COMMA,                                              // , 
	PS2SERKBD_MAKE_SPACE, PS2SERKBD_BREAK_SPACE,                                              //   
	PS2SERKBD_MAKE_LEFTSHIFT, PS2SERKBD_MAKE_W, PS2SERKBD_BREAK_W, PS2SERKBD_BREAK_LEFTSHIFT, // W 
	PS2SERKBD_MAKE_O, PS2SERKBD_BREAK_O,                                                      // o 
	PS2SERKBD_MAKE_R, PS2SERKBD_BREAK_R,                                                      // r 
	PS2SERKBD_MAKE_L, PS2SERKBD_BREAK_L,                                                      // l 
	PS2SERKBD_MAKE_D, PS2SERKBD_BREAK_D,                                                      // d 
	PS2SERKBD_MAKE_LEFTSHIFT, PS2SERKBD_MAKE_1, PS2SERKBD_BREAK_1, PS2SERKBD_BREAK_LEFTSHIFT, // ! 
	PS2SERKBD_MAKE_ENTER, PS2SERKBD_BREAK_ENTER                                               // \n
};

Ps2serkbd ps2serkbd = Ps2serkbd();

void setup() {
	Serial.begin(9600);
}

void loop() {
	for (int i = 0; i < 34; i++) {
		ps2serkbd.emit(scancodes[i]);
		delay(5);
	}

	delay(5000);
}
