
# ps2serkbd
This library allows you to use any Arduino as a keyboard under Linux.

If you have an Arduino which supports the USB HID Library, e.g. an ATmega32U4
based one, like a
[Leonardo](https://www.arduino.cc/en/Main/Arduino_BoardLeonardo) or a
[Micro](https://store.arduino.cc/arduino-micro) your best option is to use the
[Keyboard](https://www.arduino.cc/reference/en/language/functions/usb/keyboard/) 
library.

If you have a different Arduino, like an
[Uno](https://store.arduino.cc/arduino-uno-rev3) or
[Mega](https://store.arduino.cc/arduino-mega-2560-rev3) you can burn the custom
[HoodLoader2](https://github.com/NicoHood/HoodLoader2) firmware and use the
[Keyboard](https://www.arduino.cc/reference/en/language/functions/usb/keyboard/)
library.  

However, the ps2serkbd library allows you to emulate a keyboard using any
Arduino with its stock firmware, with the following caveats:
- It will only work with Linux.
- You may need to add a udev rule in some cases, see [below](#udev).
- It currently works only with the default serial port.  Additional serial ports
(for example on an Arduino Mega) and
[SoftwareSerial](https://www.arduino.cc/en/Reference/softwareSerial) will be
supported in a later version.

## Examples
- HelloWorld1 - Prints "Hello, World!" every 5 seconds using the print()
  function.
- HelloWorld2 - Prints "Hello, World!" every 5 seconds using the emit() function.
- AsciiTable - Prints a table of the printable ASCII characters every 5 seconds.

## udev
udev can override the scancode-to-keycode mapping to enable additional functions.
On Ubuntu you can see those additional mappings in
`/usr/lib/udev/hwdb.d/60-keyboard.hwdb`.  For example on my Lenovo IdeaPad Y580
the following lines from this file are applied:
```
evdev:atkbd:dmi:bvn*:bvr*:bd*:svnLENOVO*:pn*IdeaPad*:pvr*
evdev:atkbd:dmi:bvn*:bvr*:bd*:svnLENOVO*:pnS10-*:pvr*
 KEYBOARD_KEY_81=rfkill                                 # does nothing in BIOS
 KEYBOARD_KEY_83=display_off                            # BIOS toggles screen state
 KEYBOARD_KEY_b9=brightnessup                           # does nothing in BIOS
 KEYBOARD_KEY_ba=brightnessdown                         # does nothing in BIOS
 KEYBOARD_KEY_f1=camera                                 # BIOS toggles camera power
 KEYBOARD_KEY_f2=f21                                    # touchpad toggle (key alternately emits F2 and F3)
 KEYBOARD_KEY_f3=f21
```

The problem is that these rules do not differentiate between raw and translated
keyboards, so they will be applied to the ps2serkbd keyboard.  This may cause some
keys to not work as expected.  In the snippet above scancode 0xf2  is mapped to
F21, which is not a problem for a translated keyboard, because 0xf2 is not used
there, but on a raw keyboard 0xf2 is KEY_DOWN.  So KEY_DOWN can't be emitted
properly now.

These issues can be fixed by adding the following line at the top of the file
`/usr/lib/udev/rules.d/60-evdev.rules`:
```
ATTRS{name}=="AT Raw Set 2 keyboard", GOTO="evdev_end"
```
