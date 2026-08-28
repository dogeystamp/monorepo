# test runner

testr is a script for running competitive programming test cases (for example for CodeForces).

![preview](https://raw.githubusercontent.com/dogeystamp/testr/main/preview.png)

## usage

Put `.in` and corresponding `.out` files in a test directory, and have an executable file to test.
For example:
```
testr --testdir ~/sandbox/testdir --exec a.out
```

Run `testr -h` for more information.

## installation

```
pip install --user git+https://github.com/dogeystamp/testr
```
