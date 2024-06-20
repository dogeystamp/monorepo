# jpg unscrewer

Tool to manually remove JPG corruption.
You can use it to rapidly poke bytes and see the effects.

This script is provided as-is, without argparse,
so you have to set the arguments at the top of the script (sorry).

The intended use case is to first open the file in
[hed](https://github.com/fr0zn/hed), and poke addresses by visual-selecting
bytes and zeroing them all. Open an image viewer like
[nsxiv](https://github.com/nsxiv/nsxiv) that will auto-reload when the image
changes. Then, when a region seems to have an interesting effect on the image,
plug the address into this script and iterate until the image seems better.

The image that made me write this script was (mostly) fixed with changes in around 5 bytes total,
plus some color edits in GIMP.
