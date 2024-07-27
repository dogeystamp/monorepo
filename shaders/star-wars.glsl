// STAR WARS cellular automata
// ===========================
//
// an implementation of star wars (https://quuxplusone.github.io/blog/2020/06/29/star-wars-ca/)
//
// based on code for http://www.vexorian.com/2015/05/cloudy-conway.html?m=1
//
// built for use in https://github.com/markusfisch/ShaderEditor
//
// controls: tap top left to switch tool, top right to switch brush

#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif

#define TOOLZONE   > 0.8

// S_ entries mark data addresses
// x, chan, width, dec
// see rstat for more info

#define S_TOOL     0., 0, 1., 10.
#define T_FILL     0.
#define T_DEL      1.
#define T_ROTOR    2.
#define T_LATTICE  3.
#define T_WALLH    4.

#define S_BRUSH    0., 2, 1., 10.
#define BR_FINE    0.
#define BR_MED     1.
#define BR_LARGE   2.
#define BR_HUGE    3.

// ui fade out timer
#define S_UI       0., 1, 10., 100.


uniform vec2 resolution;
uniform int pointerCount;
uniform vec3 pointers[10];
uniform sampler2D backbuffer;
uniform int second;
uniform int frame;

float oneIfZero(float value) {
	return step(abs(value), 0.05);
}
float oiz(float value) {
	// one if zero alias
	return step(abs(value), 0.05);
}

vec4 get4(float x, float y) {
	return texture2D(backbuffer,
		mod(gl_FragCoord.xy + vec2(x, y), resolution) / resolution);
}

vec4 get4abs(float x, float y) {
	return texture2D(backbuffer, vec2(x, y) / resolution);
}

vec4 get4c(vec4 c) {
	return texture2D(backbuffer, c.xy / resolution);
}

vec4 evaluate(float sum, float prev) {
	vec4 cell = get4(0.0, 0.0);
	float wasAlive = 1. - step(prev, 0.9);
	float has2 = oneIfZero(sum - 2.0);
	float has3 = oneIfZero(sum - 3.0);
	float has4 = oneIfZero(sum - 4.0);
	float has5 = oneIfZero(sum - 5.0);
	// In this rule, a state-0 cell will become state 1
	// iff it has two state-1 neighbours.
	// A state-1 cell does not change if it has 3, 4 or 5
	// state-1 neighbours, otherwise it will enter state 2
	// next tick and then state 3 before dying.

	// use the a channel for representing: states are 1.0, 0.2, 0.1, 0.0.

	// 1 -> 1, 1 -> 2
	float stay = wasAlive * max(min(has3 + has4 + has5, 1.), 0.2);
	// 0 -> 1
	float become = oneIfZero(prev) * has2;
	// 2 -> 3, 3 -> 0
	float decay = (1. - wasAlive) * max(prev - .1, 0.);

	float state = max(stay, max(become, decay));
	return vec4(
		cell.g * 0.7,
		oneIfZero(state - 1.) * 0.03 + cell.g * 0.95 + oneIfZero(state - .1) * 0.1,
		oneIfZero(state - 0.2) * 0.2 + cell.g,
		state
	);

}

float get(float x, float y) {
	return 1. - step(get4(x, y).a, 0.9);
}

// store state in (x, 0)'s rgb channels.
// different decimals for different state
// avoid passing data like .99 because floating point imprecision

// pass in dec 10, 100, 1000, and so on
// chan 0, 1, 2 for rgb
// width 1., 10., 100. to control how many decimals for one datum

float rstat(float x, int chan, float width, float dec) {
	return floor(mod(get4abs(0.5 + x, 0.5)[chan] * dec, 10. * width));
}

// return delta to modified state, set to v
vec4 wstat(float x, int chan, float width, float dec, float v) {
	vec4 ret;
	ret[chan] = (v - rstat(x, chan, width, dec)) / dec;
	return ret;
}

// return a color for a state
// prev is the a in the vec4 which we keep same
vec4 colstat(float s, float prev) {
	return
		oiz(s - 0.) * vec4(0.5, 0., 0., prev) +
		oiz(s - 1.) * vec4(0.8, 0.5, 0., prev) +
		oiz(s - 2.) * vec4(0.8, 0.8, 0., prev) +
		oiz(s - 3.) * vec4(0., 0.5, 0., prev) +
		oiz(s - 4.) * vec4(0.0, 0., 0.5, prev) +
		oiz(s - 5.) * vec4(0.1, 0., 0.3, prev) +
		oiz(s - 6.) * vec4(0.5, 0., 0.5, prev) +
		oiz(s - 7.) * vec4(0.5, 0.5, 0.5, prev) +
		oiz(s - 8.) * vec4(0., 0.5, 0.5, prev) +
		oiz(s - 9.) * vec4(0., 0., 0., prev);
}

// get brush size
float getbrush() {
	float id = rstat(S_BRUSH);
	float side = max(resolution.x, resolution.y);
	return side * (
		oiz(id - 0.) * .02 +
		oiz(id - 1.) * .07 +
		oiz(id - 2.) * .15 +
		oiz(id - 3.) * .4
	);
}

void main() {
	float sum =
		get(-1.0, -1.0) +
		get(-1.0, 0.0) +
		get(-1.0, 1.0) +
		get(0.0, -1.0) +
		get(0.0, 1.0) +
		get(1.0, -1.0) +
		get(1.0, 0.0) +
		get(1.0, 1.0);

	vec2 center = resolution /2.;

	float prev = get4(0., 0.).a;

	bool switchTool = false;
	vec2 puv = vec2(1.);
	if (pointerCount > 0) {
		puv = pointers[0].xy / resolution;
		switchTool = puv.y TOOLZONE;
	}

	float tapSize = getbrush();
	float tool = rstat(S_TOOL);
	for (int n = 0; n < pointerCount; ++n) {
		if (!switchTool && abs(pointers[n].y - gl_FragCoord.y) < tapSize && tool == T_WALLH) {
			prev = 0.;
			sum = 0.;
			float c = mod(gl_FragCoord.y - .5, 6.);
			if (
				c < 4.
				&& (mod(c, 3.) == 0. || mod(c + gl_FragCoord.x - .5, 2.) == 0.)
			)
				sum = 2.;
			break;
		} else if (!switchTool && distance(pointers[n].xy, gl_FragCoord.xy) < tapSize) {
			prev = 0.;
			sum = 0.;
			if (tool == T_ROTOR) {
				vec2 modc = mod(gl_FragCoord.xy, 9.) - 0.5;
				if (abs(modc.y - 2.) + abs(modc.x - 2.) <= 1.)
					sum = 2.0;
			} else if (tool == T_LATTICE) {
			// lattice: 01101101
				if (mod(mod(gl_FragCoord.x + gl_FragCoord.y, 8.), 3.) >= 1.)
					sum = 2.;
			} else if (tool == T_DEL)
				sum = 0.;
			else if (tool == T_FILL)
				sum = 2.;
			break;
		}
	} 

	if (frame == 0)
		gl_FragColor = vec4(0.);
	else
		gl_FragColor = evaluate(sum, prev);

	vec2 uv = gl_FragCoord.xy / resolution.xy;

	float uiTimer = rstat(S_UI);
	if (gl_FragCoord.xy == vec2(0.5, 0.5)) {
		gl_FragColor = get4c(gl_FragCoord);

		if (switchTool && puv.x < 0.5) {
			if (uiTimer < 94.) {
				// change tool
				float new = mod(rstat(S_TOOL) + 1., 5.);
				gl_FragColor += wstat(S_TOOL, new);
				// show ui
				gl_FragColor += wstat(S_UI, 96.);
			}
		} else if (switchTool && puv.x > 0.5) {
			if (uiTimer < 94.) {
				// change brush size
				float new = mod(rstat(S_BRUSH) + 1., 4.);
				gl_FragColor += wstat(S_BRUSH, new);
				// show ui
				gl_FragColor += wstat(S_UI, 96.);
			}
		} else if (uiTimer > 50.)
			gl_FragColor += wstat(S_UI, uiTimer - 1.);
		else if (uiTimer <= 50.)
			gl_FragColor += wstat(S_UI, max(0., uiTimer - 15.));
	} else if (uv.x < 0.5 && uv.y TOOLZONE) {
		gl_FragColor.rgb *= 1. - uiTimer / 100.;
		vec4 statCol = colstat(rstat(S_TOOL), gl_FragColor.a);
		gl_FragColor.a = 0.;
		statCol.rgb *= uiTimer / 100.;
		gl_FragColor += statCol;
	} else if (uv.x > 0.5 && uv.y TOOLZONE) {
		gl_FragColor.rgb *= 1. - uiTimer / 100.;
		vec4 statCol = colstat(rstat(S_BRUSH), gl_FragColor.a);
		gl_FragColor.a = 0.;
		statCol.rgb *= uiTimer / 100.;
		gl_FragColor += statCol;
	}
}

