#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import urllib.request
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

LINUX_VERSION = 'v5.12'
BASE_URL = f'https://raw.githubusercontent.com/torvalds/linux/{LINUX_VERSION}'
BASEPATH = Path(__file__).parent.absolute()
TEMPLATES_DIR = BASEPATH.joinpath('templates')
SRC_DIR = BASEPATH.parent.joinpath('src')

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


def download(url, path):
    if not path.exists():
        data = urllib.request.urlopen(url).read()
        path.write_bytes(data)

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

def getScancodes():
    filename = BASEPATH.joinpath('atkbd.c')
    download(f'{BASE_URL}/drivers/input/keyboard/atkbd.c', filename)
    lines = initpp(filename)

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

def getKeycodes():
    filename = BASEPATH.joinpath('input-event-codes.h')
    download(f'{BASE_URL}/include/uapi/linux/input-event-codes.h', filename)
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

def generateHeaders():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR),
                      trim_blocks=True,
                      lstrip_blocks=True)

    context = {
        'keys': list(filter(None, keys)),
        'ascii2keycode': ascii2keycode
    }

    for filename in 'scancodes.h', 'ascii.h':
        template = env.get_template(f'{filename}.j2')
        SRC_DIR.joinpath(filename).write_text(template.render(context))

keycodes = getKeycodes()
scancodes = getScancodes()

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
    generateHeaders()
