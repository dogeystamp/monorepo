#!/usr/bin/env -S uv run --script

# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "aiohttp>=3.13.5",
#     "aioping>=0.4.0",
#     "plumbum",
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
import aiohttp
import aiohttp.client_exceptions
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

DEGRADED_COLOR = "#dd8844"
"""Color for degraded hosts."""

DOWN_COLOR = "#cc4444"
"""Color for offline hosts."""

PENDING_COLOR = "gray"
"""Color for hosts of unknown status."""

# ---------------
# TYPES
# ---------------


class HostStateUp:
    """Host is confirmed up."""


class HostStateDegraded:
    """Host is partially down."""


class HostStateDown:
    """Host is confirmed down."""


class HostStatePending:
    """No data yet, and waiting on host response."""


type HostState = HostStateUp | HostStateDegraded | HostStateDown | HostStatePending


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
    """Human-readable name."""

    pinger: "PingImplementation"
    """Object that can be used to ping this host."""

    def __hash__(self):
        return self.id.__hash__()


@dataclass
class HostGroup:
    """
    Group of hosts.

    It will be marked online if all hosts are online, offline if all hosts are
    offline, pending if any host is pending, and degraded otherwise.
    """

    name: str
    """Human-readable name."""

    hosts: list[Host]
    """Ordered list of hosts in this group."""

    def group_state(self, states: dict[Host, HostState]):
        my_states = [states[host] for host in self.hosts]
        if any(isinstance(state, HostStatePending) for state in my_states):
            return HostStatePending()
        if all(isinstance(state, HostStateDown) for state in my_states):
            return HostStateDown()
        if all(isinstance(state, HostStateUp) for state in my_states):
            return HostStateUp()
        return HostStateDegraded()


@dataclass
class EventChange:
    host: Host
    new_state: HostState


type PingerEvent = EventChange


@dataclass
class PingerState:
    """Data to coordinate between coroutines."""

    hosts: list[Host]
    groups: list[HostGroup]
    queue: asyncio.Queue[PingerEvent]
    finished: asyncio.Event
    http_session: aiohttp.ClientSession

    name_filter_rich: Callable[[str], str]
    """Function that filters host names into Rich markup."""

    name_filter: Callable[[str], str]
    """Function that filters host names into text."""


# ---------------------
# UTILITIES
# ---------------------


async def notify(msg: str):
    await notify_send("-a", "Pinger", msg)


def state_to_style(state: HostState) -> str:
    """Get the Rich style for a state."""
    match state:
        case HostStateUp():
            return f"[bold {UP_COLOR}]"
        case HostStateDown():
            return f"[bold {DOWN_COLOR}]"
        case HostStatePending():
            return f"[{PENDING_COLOR}]"
        case HostStateDegraded():
            return f"[bold {DEGRADED_COLOR}]"
        case _:
            assert_never(state)


def state_to_name(state: HostState) -> str:
    """Convert state to readable name."""
    match state:
        case HostStateUp():
            return "ONLINE"
        case HostStateDown():
            return "OFFLINE"
        case HostStatePending():
            return "(pending)"
        case HostStateDegraded():
            return "DEGRADED"
        case _:
            assert_never(state)


def state_to_name_rich(state: HostState) -> str:
    """Convert state to readable name (Rich markup)."""
    return f"{state_to_style(state)}{state_to_name(state)}[/]"


def state_to_badge(state: HostState) -> str:
    """Convert state to text badge."""
    match state:
        case HostStateUp():
            return "OK"
        case HostStateDown():
            return "!!"
        case HostStatePending():
            return "--"
        case HostStateDegraded():
            return "!~"
        case _:
            assert_never(state)


def state_to_badge_rich(state: HostState) -> str:
    """Convert state to badge in Rich console markup."""
    return f"{state_to_style(state)}{state_to_badge(state)}[/]"


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
    async def ping(self, _state: PingerState) -> HostState:
        """Ping a host once."""


@dataclass
class PingICMP(PingImplementation):
    """ICMP net ping using Unix `ping`."""

    endpoint: str
    """Network host to ping (e.g. an IP address)."""

    async def ping(self, _state) -> HostState:
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

    async def ping(self, _state: PingerState) -> HostState:
        session = _state.http_session
        try:
            async with session.get(self.url) as resp:
                resp.raise_for_status()

        except aiohttp.client_exceptions.ClientError as err:
            return HostStateDownHTTP(err=err)
        return HostStateUp()


async def ping_task(state: PingerState) -> None:
    """Setup long-running ping tasks."""

    async def ping_host(host: Host):
        """Get a single host's ping status."""
        current_state: HostState = HostStatePending()
        while not state.finished.is_set():
            new_state = await host.pinger.ping(state)
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
        host_panels: dict[Host, Panel] = {}
        for host, hstate in states.items():
            tab = Table.grid(expand=True, padding=2)
            tab.add_column(justify="left")
            tab.add_column(justify="right")
            tab.add_row(
                f"[bold]{state.name_filter_rich(host.name)}[/]",
                state_to_badge_rich(hstate),
            )
            host_panels[host] = Panel(tab, box=rich.box.SQUARE)

        group_panels: list[Panel] = []

        for group in state.groups:
            group_panels.append(
                Panel.fit(
                    Columns((host_panels[host] for host in group.hosts)),
                    title=f"[italic]{state.name_filter_rich(group.name)} {state_to_name_rich(group.group_state(states))}[/]",
                    title_align="center",
                    box=rich.box.SQUARE,
                    width=80,
                )
            )

        return Columns(group_panels)

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

    def main(self, *host_strs: str):
        async def amain():
            if len(host_strs) == 0:
                Pinger.help(self)
                return 1

            name_filter = lambda s: s  # noqa: E731
            name_filter_rich = rich.markup.escape

            if self.upper:
                name_filter = str.upper
                name_filter_rich = lambda s: rich.markup.escape(str.upper(s))  # noqa: E731

            hosts = []

            cmd_hosts = [parse_host(host) for host in host_strs]
            hosts += cmd_hosts

            async with aiohttp.ClientSession() as http_session:
                state = PingerState(
                    hosts=cmd_hosts,
                    groups=[HostGroup(name="Command Line", hosts=cmd_hosts)],
                    queue=asyncio.Queue(),
                    finished=asyncio.Event(),
                    http_session=http_session,
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
