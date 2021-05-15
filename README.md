# ps2serkbd
This library allows you to use any Arduino as a keyboard.

If you want to emulate a keyboard with an Arduino your best option is to use
the official
[Keyboard](https://www.arduino.cc/reference/en/language/functions/usb/keyboard/)
library.  However it only works with boards which support the USB HID Library,
like
[Leonardo](https://www.arduino.cc/en/Main/Arduino_BoardLeonardo) and
[Micro](https://store.arduino.cc/arduino-micro).  It doesn't work with many
popular boards such as
[Arduino Uno](https://store.arduino.cc/arduino-uno-rev3) or
[Arduino Mega](https://store.arduino.cc/arduino-mega-2560-rev3) unless you
install a custom firmware such as
[HoodLoader2](https://github.com/NicoHood/HoodLoader2).

The ps2serkbd library was created to solve this problem.  It sends keyboard
scancodes over the serial port, so it allows you to emulate a keyboard using
any Arduino, with the following caveats:
- It works only on Linux.
- You may need to add a udev rule in some cases, see [below](#udev).
- It currently works only with the default serial port.  Additional serial
ports (for example on an Arduino Mega) and
[SoftwareSerial](https://www.arduino.cc/en/Reference/softwareSerial) will be
supported in a later version.

## Host setup
On the host computer you need to attach the keyboard driver to the serial port.
Do this after the Arduino is programmed, as otherwise it will interfere with
the programming process which also uses the serial port.
For example, if your Arduino is attached to /dev/ttyACM0 after uploading the
code to it, run the command:
```
sudo inputattach --ps2serkbd /dev/ttyACM0
```
You can also run it in the background:
```
sudo inputattach --daemon --ps2serkbd /dev/ttyACM0
```

## API:
The library provides the following functions:
- emit() - sends a single scancode to the host.  This is just a wrapper over
  Serial.write().  The possible scancodes are defined in
  [src/scancodes.h](src/scancodes.h).
  ```
  ps2serkbd.emit(PS2SERKBD_MAKE_F11);  // Press the F11 key
  ps2serkbd.emit(PS2SERKBD_BREAK_F11); // Release the F11 key

  // Send Control-Alt-Delete
  ps2serkbd.emit(PS2SERKBD_MAKE_LEFTCTRL);
  ps2serkbd.emit(PS2SERKBD_MAKE_LEFTALT);
  ps2serkbd.emit(PS2SERKBD_MAKE_DELETE);
  ps2serkbd.emit(PS2SERKBD_BREAK_LEFTCTRL);
  ps2serkbd.emit(PS2SERKBD_BREAK_LEFTALT);
  ps2serkbd.emit(PS2SERKBD_BREAK_DELETE);
  ```

- press() - sends the make scancode for a character.  The possible characters
  are defined in [src/ascii.h](src/ascii.h) and in addition to them `'\t'` and
  `'\n'` are also supported.
  ```
  ps2serkbd.press('\t'); // Press (and hold) the tab key
  ps2serkbd.press('\n'); // Press (and hold) the enter key
  ps2serkbd.press('a'); // Press (and hold) a
  ps2serkbd.press('A'); // Press (and hold) shift and a
  ```

- release() - sends the break scancode for a character.  The possible
  characters are defined in [src/ascii.h](src/ascii.h) and in addition to them
  `'\t'` and `'\n'` are also supported.
  ```
  ps2serkbd.release('\t'); // Release the tab key
  ps2serkbd.release('\n'); // Release the enter key
  ps2serkbd.release('a'); // Release a
  ps2serkbd.release('A'); // Release shift and a
  ```
- print() - sends the codes for a string.
  ```
  ps2serkbd.print("Hello, world!\n");
  ```

## Examples
- [HelloWorld1](examples/HelloWorld1/HelloWorld1.ino) - Prints "Hello, World!"
  every 5 seconds using the emit() function.
- [HelloWorld2](examples/HelloWorld2/HelloWorld2.ino) - Prints "Hello, World!"
  every 5 seconds using the print() function.
- [AsciiTable](examples/AsciiTable/AsciiTable.ino) - Prints a table of the
  printable ASCII characters every 5 seconds.

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

This issue can be fixed by adding the following line at the top of the file
`/usr/lib/udev/rules.d/60-evdev.rules`:
```
ATTRS{name}=="AT Raw Set 2 keyboard", GOTO="evdev_end"
```
