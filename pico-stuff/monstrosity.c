/**
 * Copyright (c) 2020 Raspberry Pi (Trading) Ltd.
 *
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include "pico/stdlib.h"
#include "pico/stdio.h"
#include <stdio.h>
#include "hardware/gpio.h"
#include "hardware/irq.h"
#include "hardware/pwm.h"

const uint BOARD_LED_PIN = PICO_DEFAULT_LED_PIN;
const uint LED_PIN = 15;
const uint LED2_PIN = 17;
const uint BUTTON_PIN = 9;
const uint ROT_CLK = 11;
const uint ROT_DT = 10;


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

int rotCt = 0;

int main() {
	stdio_init_all();
#ifndef PICO_DEFAULT_LED_PIN
#warning picoboard/blinky example requires a board with a regular LED
#else
	gpio_set_function(LED2_PIN, GPIO_FUNC_PWM);
	uint slice_num = pwm_gpio_to_slice_num(LED2_PIN);
	pwm_config config = pwm_get_default_config();
	pwm_config_set_clkdiv(&config, 4.f);
	pwm_init(slice_num, &config, true);


    gpio_init(ROT_CLK);
    gpio_init(ROT_DT);
    gpio_set_dir(ROT_CLK, GPIO_IN);
    gpio_set_dir(ROT_DT, GPIO_IN);

    gpio_init(BOARD_LED_PIN);
    gpio_set_dir(BOARD_LED_PIN, GPIO_OUT);

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    gpio_init(BUTTON_PIN);
    gpio_set_dir(BUTTON_PIN, GPIO_IN);

	int rotClkState = gpio_get(ROT_CLK);
	int lastClkState = rotClkState;

	const int bufSz = 50;
	char buf[bufSz];
	int bufIdx = 0;

	put_morse_str(LED_PIN, "hi");
	put_morse_str(BOARD_LED_PIN, "fox");

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
		if (gpio_get(BUTTON_PIN)) {
			gpio_put(BOARD_LED_PIN, 1);
		} else {
			gpio_put(BOARD_LED_PIN, 0);
		}

		rotClkState = gpio_get(ROT_CLK);
		if (lastClkState != rotClkState && rotClkState == 1) {
			if (gpio_get(ROT_DT) != rotClkState) {
				rotCt -= 10;
			} else {
				rotCt += 10;
			}
			if (rotCt >= 256) {
				rotCt = 255;
			} else if (rotCt < 0) {
				rotCt = 0;
			}
			printf("%d\n", rotCt);
			pwm_set_gpio_level(LED2_PIN, rotCt*rotCt);
		}
		lastClkState = rotClkState;
	}
#endif
}
