#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import urllib.request

LINUX_VERSION = 'v5.12'

BASE_URL = f'https://raw.githubusercontent.com/torvalds/linux/{LINUX_VERSION}'
KEYCODES_URL = f'{BASE_URL}/include/uapi/linux/input-event-codes.h'
SCANCODES_URL = f'{BASE_URL}/drivers/input/keyboard/atkbd.c'

KEYCODES_FILE = KEYCODES_URL.split('/')[-1]
SCANCODES_FILE = SCANCODES_URL.split('/')[-1]

OUTPUT_SCANCODES = 'scancodes.h'
OUTPUT_ASCII = 'ascii.h'


def download(url, filename):
    if not os.path.exists(filename):
        data = urllib.request.urlopen(url).read()
        with open(filename, "wb") as f:
            f.write(data)

def initpp(filename):
    # Try to follow the order described in:
    # https://gcc.gnu.org/onlinedocs/cpp/Initial-processing.html

    # 1. Break the input file into lines
    with open(filename) as f:
        lines = f.readlines()

    # 2. TODO Convert trigraphs

    # 3. Merge continued lines
    processedLines = []
    multiline = False
    for line in lines:
        if not (line := line.strip()):
            multiline = False
            continue
        if not multiline:
            if line[-1] == '\\':
                multiline = True
                line = line[:-1]
            processedLines.append(line)
        else:
            if line[-1] == '\\':
                line = line[:-1]
            else:
                multiline = False
            processedLines[-1] += line

    lines = processedLines

    # 4. Replace comments with a single space
    processedLines = []
    inComment = False
    inQuote = False
    for line in lines:
        n = 0
        if not inComment:
            processedLine = []
        while n < len(line):
            if not (inComment or inQuote):
                if line[n:n+2] == '//':
                    processedLine += ' '
                    break
                elif line[n:n+2] == '/*':
                    inComment = True
                    n += 2
                else:
                    if line[n] == '"':
                        inQuote = True
                    processedLine += line[n]
                    n += 1
            elif inQuote:
                if line[n] == '\\':
                    processedLine += line[n:n+1]
                    n += 2
                else:
                    if line[n] == '"':
                        inQuote = False
                    processedLine += line[n]
                    n += 1
            elif inComment:
                if line[n:n+2] == '*/':
                    inComment = False
                    processedLine += ' '
                    n += 2
                else:
                    n += 1

        if not inComment:
            processedLines.append(''.join(processedLine))

    lines = processedLines

    return lines

def getScancodes(lines):
    lines = initpp(lines)
    scancodes = []
    inTable = False
    for line in lines:
        line = line.strip()
        if re.match('static const unsigned short atkbd_set2_keycode\[ATKBD_KEYMAP_SIZE\] = {', line):
            inTable = True
            continue

        if inTable:
            # process only lines consistng of comma-separated digits
            if not re.search('[^ ,\d]', line):
                for line in line.split(','):
                    line = line.strip()
                    if line:
                        scancodes.append(int(line))

            if line == '};':
                return scancodes

def getKeycodes(filename):
    lines = initpp(filename)
    # We are only interesed in macros of the form:
    # #define KEY_SOMETHING 0-255
    keycodes = [''] * 256
    for line in lines:
        line = re.sub('\s+', ' ', line.strip()) # Trim and squash
        if m := re.match('# ?define KEY_([^ ]+) ([1-9][0-9]*)', line):
            name = m[1]
            keycode = int(m[2])
            if keycodes[keycode]:
                raise ValueError(f'Found duplicate keycode: {keycode}')
            else:
                keycodes[keycode] = name
    return keycodes

def generateScancodes(filename, keys):
    maxLen = max([len(x[0]) for x in keys if x]) + len('_BREAK_')

    with open(filename, 'w') as f:
        f.write('#ifndef __PS2SERKBD_SCANCODES_H__\n');
        f.write('#define __PS2SERKBD_SCANCODES_H__\n');
        f.write('\n')

        spaces = ' ' * (maxLen - len('BREAK'))
        f.write(f'#define PS2SERKBD_BREAK{spaces}"\\xf0"\n');
        f.write('\n')

        for keycode in range(len(keys)):
            try:
                name, scancode = keys[keycode]
            except TypeError:
                continue

            spaces = ' ' * (maxLen - len(name))
            f.write(f'#define PS2SERKBD_{name}{spaces}"{scancode}"\n')
            spaces = ' ' * (maxLen - len(name) - len('MAKE_'))
            f.write(f'#define PS2SERKBD_MAKE_{name}{spaces}"{scancode}"\n')
            spaces = ' ' * (maxLen - len(name) - len('BREAK_'))
            if scancode.startswith('\\xe0'):
                scancode = scancode[:4] + '\\xf0' + scancode[4:]
            else:
                scancode = '\\xf0' + scancode
            f.write(f'#define PS2SERKBD_BREAK_{name}{spaces}"{scancode}"\n')
            f.write('\n')

        f.write('#endif /* !__PS2SERKBD_SCANCODES_H__ */\n');

download(KEYCODES_URL, KEYCODES_FILE)
download(SCANCODES_URL, SCANCODES_FILE)
keycodes = getKeycodes(KEYCODES_FILE)
scancodes = getScancodes(SCANCODES_FILE)

keys = keycodes[:]
for keycode in range(len(keys)):
    if scancodes.count(keycode) == 1:
        name = keys[keycode]
        scancode = scancodes.index(keycode)
        if scancode & 0x80:
            scancode &= ~0x80
            scancode = f'\\xe0\\x{scancode:02x}'
        else:
            scancode = f'\\x{scancode:02x}'
        keys[keycode] = (name, scancode)
    else:
        keys[keycode] = None

if __name__ == '__main__':
    generateScancodes(OUTPUT_SCANCODES, keys)
    print(f'{OUTPUT_SCANCODES} generated.')
