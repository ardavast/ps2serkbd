#ifndef __PS2SERKBD_H__
#define __PS2SERKBD_H__

#include "Arduino.h"
#include "scancodes.h"

class Ps2serkbd
{
public:
	Ps2serkbd(void);
	void emit(const char *scancode);
	void press(char c);
	void release(char c);
	void print(char s);
	void print(const char *s);
};

#endif /* !__PS2SERKBD_H__ */
