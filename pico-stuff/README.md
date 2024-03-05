# raspberry pi pico playground

- `morse.c`: morse blinker (with a shell over serial to send messages to blink)
- `monstrosity.c`: driver code for random components i had laying around
- `test.c`: morse code HID keyboard (needs two buttons). can use vim with it
- `tablegen.py`: helper to generate keymaps for `test.c` morse

you will need to put the raspberry pi pico sdk somewhere and export `PICO_SDK_PATH` to point to it.
also, it could be useful to export `CMAKE_EXPORT_COMPILE_COMMANDS=1` to get a `compile_commands.json`.
