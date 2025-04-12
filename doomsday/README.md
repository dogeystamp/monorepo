# doomsday

A "data science" project using [marimo](https://marimo.io/),
which is a modern Python notebook.

This takes data from a `tsv` file, runs some computations on it,
and produces graphs.

The recommended way to run this is with [uv](https://docs.astral.sh/uv/).

```
uv tool install marimo
uv run marimo edit
uv run marimo edit --watch --sandbox main.py
```

This will start the notebook in a completely reproducible way,
with all its dependencies isolated.

No data file is provided in this repository.

![preview](https://raw.githubusercontent.com/dogeystamp/monorepo/main/doomsday/picture.jpg)
