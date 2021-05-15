#include <ps2serkbd.h>

Ps2serkbd ps2serkbd = Ps2serkbd();

void setup() {
	Serial.begin(9600);
}

void loop() {
	static char s[4];

	for (int i = 32; i < 127; i++) {
		snprintf(s, 4, "%x", i / 16);
		ps2serkbd.print(s);
	}
	ps2serkbd.print("\n");

	for (int i = 32; i < 127; i++) {
		snprintf(s, 4, "%x", i % 16);
		ps2serkbd.print(s);
	}
	ps2serkbd.print("\n");

	for (int i = 32; i < 127; i++) {
		snprintf(s, 4, "%c", char(i));
		ps2serkbd.print(s);
	}
	ps2serkbd.print("\n\n");

	delay(5000);
}
