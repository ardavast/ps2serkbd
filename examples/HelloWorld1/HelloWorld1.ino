#include <ps2serkbd.h>

Ps2serkbd ps2serkbd = Ps2serkbd();

void setup() {
	Serial.begin(9600);
}

void loop() {
	ps2serkbd.print("Hello, World!\n");
	delay(5000);
}
