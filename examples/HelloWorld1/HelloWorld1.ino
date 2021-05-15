#include <ps2serkbd.h>

Ps2serkbd ps2serkbd;

void setup() {
	Serial.begin(9600);
	ps2serkbd.begin(&Serial);
}

void loop() {
	ps2serkbd.print("Hello, World!\n");
	delay(5000);
}
