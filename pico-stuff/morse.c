/**
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <stdio.h>
#include "pico/stdio.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"

const uint DOT_PERIOD_MS = 100;

const char *morse_letters[] = {
        ".-",    // A
        "-...",  // B
        "-.-.",  // C
        "-..",   // D
        ".",     // E
        "..-.",  // F
        "--.",   // G
        "....",  // H
        "..",    // I
        ".---",  // J
        "-.-",   // K
        ".-..",  // L
        "--",    // M
        "-.",    // N
        "---",   // O
        ".--.",  // P
        "--.-",  // Q
        ".-.",   // R
        "...",   // S
        "-",     // T
        "..-",   // U
        "...-",  // V
        ".--",   // W
        "-..-",  // X
        "-.--",  // Y
        "--.."   // Z
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

int main() {
	stdio_init_all();
#ifndef PICO_DEFAULT_LED_PIN
#warning picoboard/blinky example requires a board with a regular LED
#else
    // const uint LED_PIN = PICO_DEFAULT_LED_PIN;
    const uint LED_PIN = 15;
    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

	const int bufSz = 50;
	char buf[bufSz];
	int bufIdx = 0;

	put_morse_str(LED_PIN, "quick brown");

    while (1) {
		unsigned int c = getchar_timeout_us(20);
		if (c != PICO_ERROR_TIMEOUT) {
			printf("%c", c);
			if (c == 0x0d) {
				buf[bufIdx] = '\0';
				printf("\n");
				put_morse_str(LED_PIN, buf);
				printf(">>> ");
				bufIdx = 0;
			} else if (bufIdx < bufSz-1) {
				buf[bufIdx++] = c;
			}
		}
	}
#endif
}
