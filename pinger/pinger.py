#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "aioping>=0.4.0",
#     "plumbum",
#     "requests>=2.33.1",
#     "rich>=15.0.0",
# ]
#
# [tool.uv.sources]
# plumbum = { git = "https://github.com/tomerfiliba/plumbum", rev = "32fa01302a6c9302e7f2e61a560da9faea6c62ff" }
# ///

"""
Ping dashboard script.


Writing new pings
-----------------

To write a new ping implementation:
- Subclass [`PingImplementation`].
- Add a case in [`parse_host`] to instantiate your implementation.
"""

from typing import assert_never, Callable
from dataclasses import dataclass
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns
from rich.live import Live
import rich.box
import rich.markup
import asyncio
import requests
from abc import ABC, abstractmethod
from plumbum import async_local, ProcessExecutionError, cli
from urllib.parse import urlparse

ping = async_local["ping"]
notify_send = async_local["notify-send"]

# ---------------
# CONSTANTS
# ---------------

WAIT_TIME = 10
"""Seconds to wait between healthchecks."""


UP_COLOR = "#44cc44"
"""Color for online hosts."""

DOWN_COLOR = "#cc4444"
"""Color for offline hosts."""

PENDING_COLOR = "gray"
"""Color for hosts of unknown status."""

# ---------------
# TYPES
# ---------------


class HostStateUp:
    """Host is confirmed up."""


class HostStateDown:
    """Host is confirmed down."""


class HostStatePending:
    """No data yet, and waiting on host response."""


type HostState = HostStateUp | HostStateDown | HostStatePending


@dataclass
class HostStateDownICMP(HostStateDown):
    err: Exception


@dataclass
class HostStateDownHTTP(HostStateDown):
    err: Exception


@dataclass
class Host:
    """Information about a healthcheck target."""

    id: str
    """Unique ID for this target (not necessarily a network hostname)."""

    name: str
    """Human readable name."""

    pinger: "PingImplementation"
    """Object that can be used to ping this host."""

    def __hash__(self):
        return self.id.__hash__()


@dataclass
class EventChange:
    host: Host
    new_state: HostState


type PingerEvent = EventChange


@dataclass
class PingerState:
    """Data to coordinate between coroutines."""

    hosts: list[Host]
    queue: asyncio.Queue[PingerEvent]
    finished: asyncio.Event

    name_filter_rich: Callable[[str], str]
    """Function that filters host names into Rich markup."""

    name_filter: Callable[[str], str]
    """Function that filters host names into text."""


# ---------------------
# UTILITIES
# ---------------------


async def notify(msg: str):
    await notify_send("-a", "Pinger", msg)


def state_to_name(state: HostState) -> str:
    """Convert state to readable name."""
    match state:
        case HostStateUp():
            return "UP"
        case HostStateDown():
            return "DOWN"
        case HostStatePending():
            return "...."
        case _:
            assert_never(state)


def state_to_badge(state: HostState) -> str:
    """Convert state to badge in Rich console markup."""

    def wrap(s: str):
        # no-op for now, but can be used to turn `OK` into `[OK]`
        return s

    match state:
        case HostStateUp():
            return wrap(f"[bold {UP_COLOR}]OK[/]")
        case HostStateDown():
            return wrap(f"[bold {DOWN_COLOR}]!![/]")
        case HostStatePending():
            return wrap(f"[bold {PENDING_COLOR}]--[/]")
        case _:
            assert_never(state)


def parse_host(host: str) -> Host:
    """
    Parse a host string into a [Host] object.

    Use a hash symbol to set a friendly name for the host.
    """
    parts = urlparse(host)
    name = parts.fragment or host

    pinger: PingImplementation | None = None

    if parts.scheme in ("http", "https"):
        # http healthcheck
        pinger = PingHTTP(url=host)
    elif parts.scheme == "":
        # ICMP ping
        pinger = PingICMP(endpoint=parts.path)
    else:
        raise ValueError(f"Couldn't parse host: '{host}'")

    assert pinger is not None
    return Host(name=name, id=host, pinger=pinger)


# ------------------------
# PING IMPLEMENTATIONS
# ------------------------


class PingImplementation(ABC):
    """Pinger, each instance pings one host."""

    @abstractmethod
    async def ping(self) -> HostState:
        """Ping a host once."""


@dataclass
class PingICMP(PingImplementation):
    """ICMP net ping using Unix `ping`."""

    endpoint: str
    """Network host to ping (e.g. an IP address)."""

    async def ping(self) -> HostState:
        try:
            await ping("-c", "1", "--", self.endpoint)
            return HostStateUp()
        except ProcessExecutionError as err:
            return HostStateDownICMP(err=err)


@dataclass
class PingHTTP(PingImplementation):
    """HTTP GET healthcheck."""

    url: str
    """URL to check."""

    async def ping(self) -> HostState:
        try:
            r = requests.get(self.url)
            r.raise_for_status()
        except requests.exceptions.RequestException as err:
            return HostStateDownHTTP(err=err)
        return HostStateUp()


async def ping_task(state: PingerState) -> None:
    """Setup long-running ping tasks."""

    async def ping_host(host: Host):
        """Get a single host's ping status."""
        current_state: HostState = HostStatePending()
        while not state.finished.is_set():
            new_state = await host.pinger.ping()
            if not isinstance(new_state, type(current_state)):
                current_state = new_state
                await state.queue.put(EventChange(host=host, new_state=new_state))
            await asyncio.sleep(WAIT_TIME)

    tasks = dict()

    async with asyncio.TaskGroup() as tg:
        for host in state.hosts:
            tasks[host] = tg.create_task(ping_host(host))


# -----------------
# RENDERING TUI
# -----------------


async def display_task(state: PingerState):
    states: dict[Host, HostState] = {host: HostStatePending() for host in state.hosts}

    def render_dashboard():
        """Render dashboard."""
        panels = []
        for host, hstate in states.items():
            tab = Table.grid(expand=True, padding=2)
            tab.add_column(justify="left")
            tab.add_column(justify="right")
            tab.add_row(
                f"[bold]{state.name_filter_rich(host.name)}[/]",
                state_to_badge(hstate),
            )
            panels.append(Panel(tab, box=rich.box.SQUARE))
        return Columns(panels)

    with Live(render_dashboard(), refresh_per_second=4, screen=True) as live:
        while not state.finished.is_set():
            event = await state.queue.get()
            match event:
                case EventChange(host=host, new_state=new_state):
                    old_state = states[host]
                    states[host] = new_state
                    if not isinstance(old_state, HostStatePending) or isinstance(
                        new_state, HostStateDown
                    ):
                        await notify(
                            f"{state.name_filter(host.name)} is now {state_to_name(new_state)}"
                        )
            live.update(render_dashboard())


# ------------------------
# MAIN ENTRY
# ------------------------


class Pinger(cli.Application):
    upper = cli.Flag(
        ["-U", "--upper"],
        help="Display all names uppercase. Improves coolness of dashboard.",
        default=False,
    )

    def main(self, *hosts: str):
        async def amain():
            if len(hosts) == 0:
                Pinger.help(self)
                return 1

            name_filter = lambda s: s  # noqa: E731
            name_filter_rich = rich.markup.escape

            if self.upper:
                name_filter = str.upper
                name_filter_rich = lambda s: rich.markup.escape(str.upper(s))  # noqa: E731

            state = PingerState(
                hosts=[parse_host(host) for host in hosts],
                queue=asyncio.Queue(),
                finished=asyncio.Event(),
                name_filter=name_filter,
                name_filter_rich=name_filter_rich,
            )

            async with asyncio.TaskGroup() as tg:
                tg.create_task(display_task(state))
                tg.create_task(ping_task(state))

        asyncio.run(amain())


if __name__ == "__main__":
    try:
        Pinger.run()
    except KeyboardInterrupt:
        pass
