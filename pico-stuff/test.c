/**
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include "device/usbd.h"
#include "hardware/gpio.h"
#include "pico/stdio.h"
#include "pico/stdlib.h"
#include "tusb.h"
#include "usb_descriptors.h"
#include <stdint.h>
#include <stdio.h>

#define max(X, Y) ((X) > (Y) ? (X) : (Y))
#define min(X, Y) ((X) < (Y) ? (X) : (Y))

const uint DOT_PERIOD_MS = 100;
// wait this time before registering a morse letter
const uint MORSE_WAIT_MS = DOT_PERIOD_MS * 3;

const char *morse_letters[] = {
	".-",	// A
	"-...", // B
	"-.-.", // C
	"-..",	// D
	".",	// E
	"..-.", // F
	"--.",	// G
	"....", // H
	"..",	// I
	".---", // J
	"-.-",	// K
	".-..", // L
	"--",	// M
	"-.",	// N
	"---",	// O
	".--.", // P
	"--.-", // Q
	".-.",	// R
	"...",	// S
	"-",	// T
	"..-",	// U
	"...-", // V
	".--",	// W
	"-..-", // X
	"-.--", // Y
	"--.."	// Z
};

void put_morse_letter(uint led_pin, const char *pattern) {
	for (; *pattern; ++pattern) {
		gpio_put(led_pin, 1);
		if (*pattern == '.')
			sleep_ms(DOT_PERIOD_MS);
		else
			sleep_ms(DOT_PERIOD_MS * 3);
		gpio_put(led_pin, 0);
		sleep_ms(DOT_PERIOD_MS * 1);
	}
	sleep_ms(DOT_PERIOD_MS * 2);
}

void put_morse_str(uint led_pin, char *str) {
	for (; *str; ++str) {
		if (*str >= 'A' && *str <= 'Z') {
			put_morse_letter(led_pin, morse_letters[*str - 'A']);
		} else if (*str >= 'a' && *str <= 'z') {
			put_morse_letter(led_pin, morse_letters[*str - 'a']);
		} else if (*str == ' ') {
			sleep_ms(DOT_PERIOD_MS * 4);
		}
	}
}

// decodes a letter
char morseDecode(char *code) {
	// flat binary tree (see gentable.py)
	const char morseTable[] =
		"**ETIANMSURWDKGOHVF\eL\bPJBXCYZQ* "
		"54*3***2*******16*******7***8*90************?********.**************"
		"\n**************,*************";

	int tableIdx = 1;

	for (; *code && tableIdx < sizeof(morseTable) / sizeof(char) - 1; code++) {
		tableIdx *= 2;
		if (*code == '-') {
			tableIdx += 1;
		}
	}

	return morseTable[tableIdx];
}

const uint DEBOUNCE_CHECK_MS = 5;
const uint DEBOUNCE_PRESS_MS = 10;
const uint DEBOUNCE_RELEASE_MS = 50;

typedef struct DebounceState {
	bool pressed;
	bool changed;

	// ms timestamp of last change
	uint64_t lastChange;
	// ms since last change
	uint64_t sinceChange;
	// ms timestamp of last check
	uint64_t lastCheck;
	// countdown timer
	uint count;
} DebounceState;

// call this in the main loop
void debounce_get(bool rawState, DebounceState *state) {
	uint time_ms = time_us_64() / 1000;

	if (state->lastChange == 0)
		state->lastChange = time_ms;
	state->sinceChange = time_ms - state->lastChange;

	state->changed = false;

	if (time_ms - state->lastCheck < DEBOUNCE_CHECK_MS) {
		return;
	}
	state->lastCheck = time_ms;

	if (rawState == state->pressed) {
		// set timer when state is stable
		state->count = state->pressed ? DEBOUNCE_RELEASE_MS / DEBOUNCE_CHECK_MS
									  : DEBOUNCE_PRESS_MS / DEBOUNCE_CHECK_MS;
	} else {
		// process change
		if (--state->count == 0) {
			// timer expires
			state->pressed = rawState;
			state->changed = true;
			state->lastChange = time_ms;
			state->count = state->pressed
							   ? DEBOUNCE_RELEASE_MS / DEBOUNCE_CHECK_MS
							   : DEBOUNCE_PRESS_MS / DEBOUNCE_CHECK_MS;
		}
	}

	return;
}

static void send_hid_report(uint8_t report_id, char key) {
	if (!tud_ready())
		return;

	switch (report_id) {
	case REPORT_ID_KEYBOARD: {
		// counter for how many null reports to send
		// idk why sending less makes it register as a continuous keypress
		// sometimes
		const uint NULL_REPORTS = 15;
		static uint nullCounter = NULL_REPORTS;
		if (key) {
			uint8_t keycode[6] = {0};
			if ('A' <= key && 'Z' >= key) {
				keycode[0] = HID_KEY_A + (key - 'A');
			} else if ('1' <= key && key <= '9') {
				keycode[0] = HID_KEY_1 + (key - '1');
			} else {
				switch (key) {
				case '0':
					// 0 is after rather than before like in ASCII so special
					// treatment here
					keycode[0] = HID_KEY_0;
					break;
				case '\n':
					keycode[0] = HID_KEY_ENTER;
					break;
				case '\b':
					keycode[0] = HID_KEY_BACKSPACE;
					break;
				case '\e':
					keycode[0] = HID_KEY_ESCAPE;
					break;
				case ' ':
					keycode[0] = HID_KEY_SPACE;
					break;
				}
			}

			tud_hid_keyboard_report(REPORT_ID_KEYBOARD, 0, keycode);
			nullCounter = NULL_REPORTS;
		} else {
			if (nullCounter > 0) {
				nullCounter--;
				// this print statement adds a necessary delay for the null reports
				printf("sent null %d\n", nullCounter);
				tud_hid_keyboard_report(REPORT_ID_KEYBOARD, 0, NULL);
			}
		}
		break;
	}
	default:
		break;
	}
}

// Invoked when sent REPORT successfully to host
// Application can use this to send the next report
// Note: For composite reports, report[0] is report ID
void tud_hid_report_complete_cb(uint8_t instance, uint8_t const *report,
								uint16_t len) {
	(void)instance;
	(void)len;

	uint8_t next_report_id = report[0] + 1;

	if (next_report_id < REPORT_ID_COUNT) {
		// send_hid_report(next_report_id, board_button_read());
	}
}

const uint PIN_DASH = 17;
const uint PIN_DOT = 16;

#define BUF_LEN 50

// return letter read
char morse_task(void) {
	static DebounceState dotState = {0};
	static DebounceState dashState = {0};

	static char buf[BUF_LEN + 1];
	buf[BUF_LEN] = '\0';
	static uint bufIdx = 0;

	debounce_get(!gpio_get(PIN_DOT), &dotState);
	debounce_get(!gpio_get(PIN_DASH), &dashState);

	uint64_t sincePress = min(dotState.sinceChange, dashState.sinceChange);

	if (bufIdx < BUF_LEN) {
		if (dotState.pressed && dotState.changed) {
			buf[bufIdx++] = '.';
		} else if (dashState.pressed && dashState.changed) {
			buf[bufIdx++] = '-';
		}
	}

	char c = '\0';

	if (!dotState.pressed && !dashState.pressed) {
		if (sincePress >= MORSE_WAIT_MS && bufIdx != 0) {
			buf[bufIdx] = '\0';
			c = morseDecode(buf);
			printf("%c", c);

			if (c == '\b') {
				printf(" \b");
			}

			bufIdx = 0;
		}
	}

	if (dotState.pressed || dashState.pressed) {
		if (tud_suspended()) {
			tud_remote_wakeup();
		}
	}

	return c;
}

// Invoked when received SET_REPORT control request or
// received data on OUT endpoint ( Report ID = 0, Type = 0 )
void tud_hid_set_report_cb(uint8_t instance, uint8_t report_id,
						   hid_report_type_t report_type, uint8_t const *buffer,
						   uint16_t bufsize) {
	(void)instance;
}

// Invoked when received GET_REPORT control request
// Application must fill buffer report's content and return its length.
// Return zero will cause the stack to STALL request
uint16_t tud_hid_get_report_cb(uint8_t instance, uint8_t report_id,
							   hid_report_type_t report_type, uint8_t *buffer,
							   uint16_t reqlen) {
	// TODO not Implemented
	(void)instance;
	(void)report_id;
	(void)report_type;
	(void)buffer;
	(void)reqlen;

	return 0;
}

int main(void) {
	stdio_init_all();
#ifndef PICO_DEFAULT_LED_PIN
#warning picoboard/blinky example requires a board with a regular LED
#else
	const uint LED_PIN = PICO_DEFAULT_LED_PIN;
	gpio_init(LED_PIN);
	gpio_set_dir(LED_PIN, GPIO_OUT);
#endif

	tusb_init();

	put_morse_str(LED_PIN, "a");

	gpio_init(PIN_DASH);
	gpio_init(PIN_DOT);
	gpio_set_dir(PIN_DASH, GPIO_IN);
	gpio_pull_up(PIN_DASH);
	gpio_set_dir(PIN_DOT, GPIO_IN);
	gpio_pull_up(PIN_DOT);

	while (1) {
		tud_task();

		char c = morse_task();
		send_hid_report(REPORT_ID_KEYBOARD, c);
	}
}
