#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import urllib.request
from pathlib import Path

from jinja2 import Template

LINUX_VERSION = 'v5.12'

BASE_URL = f'https://raw.githubusercontent.com/torvalds/linux/{LINUX_VERSION}'
KEYCODES_URL = f'{BASE_URL}/include/uapi/linux/input-event-codes.h'
SCANCODES_URL = f'{BASE_URL}/drivers/input/keyboard/atkbd.c'

BASEPATH = Path(__file__).parent.absolute()
KEYCODES_FILE = BASEPATH.joinpath('input-event-codes.h')
SCANCODES_FILE = BASEPATH.joinpath('atkbd.c')
OUTPUT_SCANCODES_TEMPLATE = BASEPATH.joinpath('scancodes.template.h')
TEMPLATES_DIR = BASEPATH.joinpath('templates')
OUTPUT_SCANCODES = BASEPATH.parent.joinpath('src', 'scancodes.h')
OUTPUT_ASCII = BASEPATH.parent.joinpath('src', 'ascii.h')

ascii2keycode = [                                                       # Dec
    'SPACE',     '1',          'APOSTROPHE', '3',          '4',         # 32 - 36
    '5',         '7',          'APOSTROPHE', '9',          '0',         # 37 - 41
    '8',         'EQUAL',      'COMMA',      'MINUS',      'DOT',       # 42 - 46
    'SLASH',     '0',          '1',          '2',          '3',         # 47 - 51
    '4',         '5',          '6',          '7',          '8',         # 52 - 56
    '9',         'SEMICOLON',  'SEMICOLON',  'COMMA',      'EQUAL',     # 57 - 61
    'DOT',       'SLASH',      '2',          'A',          'B',         # 62 - 66
    'C',         'D',          'E',          'F',          'G',         # 67 - 71
    'H',         'I',          'J',          'K',          'L',         # 72 - 76
    'M',         'N',          'O',          'P',          'Q',         # 77 - 81
    'R',         'S',          'T',          'U',          'V',         # 82 - 86
    'W',         'X',          'Y',          'Z',          'LEFTBRACE', # 87 - 91
    'BACKSLASH', 'RIGHTBRACE', '6',          'MINUS',      'GRAVE',     # 92 - 96
    'A',         'B',          'C',          'D',          'E',         # 97 - 101
    'F',         'G',          'H',          'I',          'J',         # 102 - 106
    'K',         'L',          'M',          'N',          'O',         # 107 - 111
    'P',         'Q',          'R',          'S',          'T',         # 112 - 116
    'U',         'V',          'W',          'X',          'Y',         # 117 - 121
    'Z',         'LEFTBRACE',  'BACKSLASH',  'RIGHTBRACE', 'GRAVE'      # 122 - 126
]

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
    lines = [line.strip() for line in lines]

    # 2. Convert trigraphs
    for old, new in (
        ('??(', '['),
        ('??)', ']'),
        ('??<', '{'),
        ('??>', '}'),
        ('??=', '#'),
        ('??/', '\\'),
        ("??'", '^'),
        ('??!', '|'),
        ('??-', '~')
    ):
        lines = [line.replace(old, new) for line in lines]

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
            # Process only lines consistng of comma-separated digits
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
    template = Template(Path(TEMPLATES_DIR).joinpath('scancodes.h.j2').read_text(),
                        trim_blocks=True)
    with open(filename, 'w') as f:
        f.write(template.render({'keys': list(filter(None, keys)),
                                 'ascii2keycode': ascii2keycode}))

#    indent = (len('#define PS2SERKBD_BREAK_') +
#              max([len(x[0]) for x in keys if x]))

def generateAscii(filename, keys):
    template = Template(Path(TEMPLATES_DIR).joinpath('ascii.h.j2').read_text(),
                        trim_blocks=True, lstrip_blocks=True)
    with open(filename, 'w') as f:
        f.write(template.render({'ascii2keycode': ascii2keycode}))

if not KEYCODES_FILE.exists():
    download(KEYCODES_URL, KEYCODES_FILE)

if not SCANCODES_FILE.exists():
    download(SCANCODES_URL, SCANCODES_URL)

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
    generateAscii(OUTPUT_ASCII, keys)
    print(f'{OUTPUT_ASCII} generated.')
