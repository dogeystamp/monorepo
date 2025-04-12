# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "marimo>=0.12.8",
#   "matplotlib==3.10.1",
#   "numpy==2.2.4",
#   "polars==1.27.1",
#   "polars-ds==0.8.3",
#   "sympy==1.13.3",
#   "watchdog>=6.0.0",
# ]
# ///

import marimo

__generated_with = "0.12.8"
app = marimo.App(width="medium")


@app.cell
def _():
    """Imports."""

    import polars as pl
    import polars_ds as pds
    import matplotlib.pyplot as plt
    import marimo as mo
    import numpy as np
    import sympy as sp
    return mo, np, pds, pl, plt, sp


@app.cell
def _(conv_n, pds, pl):
    """Parse data."""

    data = pl.read_csv(
        "xx.tsv", separator="\t", truncate_ragged_lines=True, quote_char=None
    )
    data.columns = ["epoch", "rating", "good", "bad"]

    data = data.select(
        "epoch",
        pl.from_epoch("epoch").alias("timestamp"),
        "rating",
        pds.convolve(
            "rating", [1 / conv_n.value] * conv_n.value, mode="same"
        ).alias("smooth_rating"),
    ).with_row_index()

    n_rows = data.select(pl.len()).item()

    data
    return data, n_rows


@app.cell
def _(mo, n_rows):
    mo.md(f"Number of entries: **{n_rows}**")
    return


@app.cell
def _(data, plt):
    """Graph raw data."""

    def plot_levels():
        plt.axhline(y=2, color="orange", linestyle=":")
        plt.axhline(y=3, color="b", linestyle=":")
        plt.axhline(y=4, color="g", linestyle=":")

    plot_levels()
    plt.xticks(rotation=45)
    plt.plot(*data.select("timestamp", "rating").get_columns())
    return (plot_levels,)


@app.cell
def _(data, mo, np, sp):
    """Compute best fit line."""

    b, m = (
        np.polynomial.polynomial.Polynomial.fit(
            *data.select("epoch", "rating").get_columns(), 1
        )
        .convert()
        .coef
    )
    x = sp.Symbol("x")
    line_eq = m * x + b


    def line(v):
        return sp.N(line_eq.subs(x, v))


    mo.vstack((mo.md("### Trendline"), line_eq))
    return b, line, line_eq, m, x


@app.cell
def _(mo):
    conv_n = mo.ui.slider(3, 365, label="Convolution window size", show_value=True, value=28)
    conv_n
    return (conv_n,)


@app.cell
def _(
    conv_n,
    data,
    display,
    doomsday,
    line,
    n_rows,
    pl,
    plot_levels,
    plt,
    threshold,
):
    """Graph smoothed data."""

    plt.xticks(rotation=45)
    plot_levels()

    _df = data.filter(
        pl.col("index") >= conv_n.value, n_rows - pl.col("index") > conv_n.value
    )

    _min_epoch = _df.get_column("epoch").min()
    _max_epoch = _df.get_column("epoch").max()
    _min_ts = _df.get_column("timestamp").min()
    _max_ts = _df.get_column("timestamp").max()

    plt.plot(*_df.select("timestamp", "smooth_rating").get_columns())
    plt.plot([_min_ts, _max_ts], [line(_min_epoch), line(_max_epoch)])

    # doomsday
    if display.value:
        plt.plot([doomsday], [threshold.value], "ro")
        plt.axhline(threshold.value, color="gray", linestyle="--")

    plt.gca()
    return


@app.cell
def _(line_eq, mo, sp, threshold):
    """Compute doomsday."""

    from datetime import datetime

    doomsday = datetime.fromtimestamp(int(sp.solve(line_eq - threshold.value)[0]))
    mo.md(f"""
    # Doomsday

    # **{doomsday}**
    """)
    return datetime, doomsday


@app.cell
def _(mo):
    threshold = mo.ui.slider(0, 4, 0.1, label="Doomsday threshold", value=0)
    display = mo.ui.checkbox(label="Display doomsday on graph")
    threshold, display
    return display, threshold


if __name__ == "__main__":
    app.run()
