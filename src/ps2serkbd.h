#ifndef __PS2SERKBD_H__
#define __PS2SERKBD_H__

#include "Arduino.h"
#include "scancodes.h"

class Ps2serkbd
{
public:
	Ps2serkbd(void);
	void begin(Stream *stream);
	void emit(const char *scancode);
	void press(char c);
	void release(char c);
	void print(const char *s, unsigned long charDelay = 5,
		   unsigned long breakDelay = 0);
private:
	Stream *stream;
};

#endif /* !__PS2SERKBD_H__ */
