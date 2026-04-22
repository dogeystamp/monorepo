# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "ics==0.7.2",
# ]
# ///

import marimo

__generated_with = "0.15.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from ics import Calendar
    from pathlib import Path
    return Calendar, Path, mo


@app.cell
def _(Path):
    OUT_DIR = Path("./output")
    IN_ICS = Path("./events.ics")
    return IN_ICS, OUT_DIR


@app.cell
def _(Calendar, IN_ICS):
    calendar = Calendar(IN_ICS.read_text())
    calendar
    return (calendar,)


@app.cell
def _(calendar, mo):
    mo.inspect(list(calendar.events)[0])
    return


@app.cell
def _(calendar):
    import itertools
    s = sorted(calendar.events, key=lambda x: list(x.categories)[0])
    grouped_events = itertools.groupby(s, key=lambda x : list(x.categories)[0])
    calendars = [(k, set(v)) for k, v in grouped_events]
    calendars
    return (calendars,)


@app.cell
def _(mo):
    generate_btn = mo.ui.run_button(label="Generate calendars")
    generate_btn
    return (generate_btn,)


@app.cell
def _(Calendar, OUT_DIR, calendars, generate_btn):
    if generate_btn.value:
        OUT_DIR.mkdir(exist_ok=True)
        for event_type, events in calendars:
            out_file = OUT_DIR / (event_type + ".ics")
            specific_cal = Calendar(events=events)
            out_file.write_text(specific_cal.serialize())
    return


if __name__ == "__main__":
    app.run()
