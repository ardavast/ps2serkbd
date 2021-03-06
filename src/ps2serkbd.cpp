#include "ps2serkbd.h"

PROGMEM static const char asciiMap[95] = {
	'\x29', '\x16', '\x52', '\x26', '\x25',
	'\x2e', '\x3d', '\x52', '\x46', '\x45',
	'\x3e', '\x55', '\x41', '\x4e', '\x49',
	'\x4a', '\x45', '\x16', '\x1e', '\x26',
	'\x25', '\x2e', '\x36', '\x3d', '\x3e',
	'\x46', '\x4c', '\x4c', '\x41', '\x55',
	'\x49', '\x4a', '\x1e', '\x1c', '\x32',
	'\x21', '\x23', '\x24', '\x2b', '\x34',
	'\x33', '\x43', '\x3b', '\x42', '\x4b',
	'\x3a', '\x31', '\x44', '\x4d', '\x15',
	'\x2d', '\x1b', '\x2c', '\x3c', '\x2a',
	'\x1d', '\x22', '\x35', '\x1a', '\x54',
	'\x5d', '\x5b', '\x36', '\x4e', '\x0e',
	'\x1c', '\x32', '\x21', '\x23', '\x24',
	'\x2b', '\x34', '\x33', '\x43', '\x3b',
	'\x42', '\x4b', '\x3a', '\x31', '\x44',
	'\x4d', '\x15', '\x2d', '\x1b', '\x2c',
	'\x3c', '\x2a', '\x1d', '\x22', '\x35',
	'\x1a', '\x54', '\x5d', '\x5b', '\x0e',
};

Ps2serkbd::Ps2serkbd(void)
{
}

void Ps2serkbd::begin(Stream *stream)
{
	this->stream = stream;
}

bool isAsciiShift(char c)
{
        return (
	    c >= 33 && c <= 38   // !"#$%&
	 || c >= 40 && c <= 43   // ()*+
	 || c >= 62 && c <= 90   // >?@ABCDEFGHIJKLMNOPQRSTUVWXYZ
	 || c >= 123 && c <= 126 // {|}~
	 || c == 58              // :
	 || c == 60              // <
	 || c == 94              // ^
	 || c == 95              // _
	);
}

void Ps2serkbd::emit(const char *scancode)
{
	stream->write(scancode);
}

void Ps2serkbd::press(char c)
{
	if (c == '\t') {
		stream->write(PS2SERKBD_MAKE_TAB);
	} else if (c == '\n') {
		stream->write(PS2SERKBD_MAKE_ENTER);
	} else if (c < 32 || c > 126) {
		return;
	} else {
        	if (isAsciiShift(c)) {
			stream->write(PS2SERKBD_MAKE_LEFTSHIFT);
		}

		stream->write(pgm_read_byte(asciiMap + (c - 32)));
	}
}

void Ps2serkbd::release(char c)
{
	if (c == '\t') {
		stream->write(PS2SERKBD_BREAK_TAB);
	} else if (c == '\n') {
		stream->write(PS2SERKBD_BREAK_ENTER);
	} else if (c < 32 || c > 126) {
		return;
	} else {
		stream->write("\xf0");
		stream->write(pgm_read_byte(asciiMap + (c - 32)));

        	if (isAsciiShift(c)) {
			stream->write(PS2SERKBD_BREAK_LEFTSHIFT);
		}
	}
}

void Ps2serkbd::print(const char *s, unsigned long charDelay,
		      unsigned long breakDelay)
{
	for (; *s; s++) {
		press(*s);
		delay(breakDelay);
		release(*s);
		delay(charDelay);
	}
}
