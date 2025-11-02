#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import logging
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence, Tuple, Union
from urllib.parse import urlparse

import yaml
from telethon import TelegramClient, events
from telethon.errors import RPCError
from telethon.sessions import StringSession
from telethon.utils import get_peer_id


LOGGER = logging.getLogger(__name__)


ChatIdentifier = Union[int, str]


@dataclass(frozen=True)
class WatchRule:
    sources: List[ChatIdentifier]
    forward_to: List[ChatIdentifier]
    include_service_messages: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WatchRule":
        sources_raw = data.get("sources")
        if sources_raw is None:
            source_single = (
                data.get("source")
                or data.get("source_chat_id")
                or data.get("source_chat")
            )
            if source_single is None:
                raise ValueError("watch entry must include source or sources")
            sources_list = [source_single]
        elif isinstance(sources_raw, Iterable) and not isinstance(
            sources_raw, (str, bytes)
        ):
            sources_list = list(sources_raw)
        else:
            raise ValueError("sources must be a list of chat identifiers")

        normalized_sources = [
            _normalize_chat_identifier(item) for item in sources_list
        ]
        if not normalized_sources:
            raise ValueError("sources list cannot be empty")

        forward_to_raw = data.get("forward_to")
        if not isinstance(forward_to_raw, Iterable) or isinstance(
            forward_to_raw, (str, bytes)
        ):
            raise ValueError("forward_to must be a list of chat identifiers")

        destinations = [
            _normalize_chat_identifier(item) for item in forward_to_raw
        ]
        if not destinations:
            raise ValueError("forward_to must contain at least one destination")

        include_service_messages = bool(
            data.get("include_service_messages", False)
        )
        return cls(
            sources=normalized_sources,
            forward_to=destinations,
            include_service_messages=include_service_messages,
        )


@dataclass(frozen=True)
class ResolvedDestination:
    target: Any
    label: str


@dataclass(frozen=True)
class ResolvedWatch:
    rule: WatchRule
    destinations: Tuple[ResolvedDestination, ...]
    label: str


@dataclass(frozen=True)
class AppConfig:
    api_id: int
    api_hash: str
    session: Union[StringSession, str]
    watch_rules: List[WatchRule]


def _normalize_chat_identifier(value: object) -> ChatIdentifier:
    if isinstance(value, bool):
        raise ValueError("boolean is not a valid chat identifier")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            raise ValueError("chat identifier cannot be empty")

        if candidate.startswith(("http://", "https://")):
            parsed = urlparse(candidate)
            host = parsed.netloc.lower()
            if host.endswith("t.me") or host.endswith("telegram.me"):
                path = parsed.path.strip("/")
                segments = [segment for segment in path.split("/") if segment]
                if not segments:
                    raise ValueError("URL does not contain chat information")
                if segments[0] == "c" and len(segments) >= 2 and segments[1].isdigit():
                    return int(f"-100{segments[1]}")
                candidate = segments[0]

        if candidate.startswith("@"):
            return candidate

        try:
            return int(candidate)
        except ValueError:
            return f"@{candidate}"

    raise ValueError("chat identifier must be a string or integer")


def _identifier_label(
    identifier: ChatIdentifier, entity: Any | None = None
) -> str:
    if entity is not None:
        username = getattr(entity, "username", None)
        title = getattr(entity, "title", None)
        if username:
            return f"@{username}"
        if title:
            return title
    if isinstance(identifier, str):
        return identifier
    return str(identifier)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Telegram forwarder using a user account (Telethon)"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        default=pathlib.Path("config.yaml"),
        help="Path to the YAML configuration file",
    )
    return parser.parse_args()


def load_config(config_path: pathlib.Path) -> AppConfig:
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except FileNotFoundError as err:
        raise SystemExit(f"Config file not found: {config_path}") from err
    except yaml.YAMLError as err:
        raise SystemExit(f"Failed to parse YAML config: {err}") from err

    if not isinstance(data, dict):
        raise SystemExit("Config root must be a mapping")

    try:
        api_id = int(data["api_id"])
    except (KeyError, ValueError, TypeError) as err:
        raise SystemExit("api_id must be provided as an integer") from err

    api_hash = data.get("api_hash")
    if not api_hash or not isinstance(api_hash, str):
        raise SystemExit("api_hash must be provided as a string")

    session_string = data.get("session_string")
    session_file = data.get("session_file")
    session: Union[StringSession, str]

    if session_string:
        if not isinstance(session_string, str):
            raise SystemExit("session_string must be a string")
        session = StringSession(session_string.strip())
    elif session_file:
        session_path = pathlib.Path(session_file)
        if not session_path.is_absolute():
            session_path = (config_path.parent / session_path).resolve()
        session = str(session_path)
    else:
        raise SystemExit("Either session_string or session_file must be provided")

    watch_entries = data.get("watch_list")
    if not isinstance(watch_entries, Sequence) or not watch_entries:
        raise SystemExit("watch_list must be a non-empty list of watch rules")

    try:
        rules = [WatchRule.from_dict(entry) for entry in watch_entries]
    except ValueError as err:
        raise SystemExit(f"Invalid watch rule: {err}") from err

    return AppConfig(
        api_id=api_id,
        api_hash=api_hash,
        session=session,
        watch_rules=rules,
    )


async def resolve_watch_rules(
    client: TelegramClient, rules: Iterable[WatchRule]
) -> Dict[int, ResolvedWatch]:
    watch_map: Dict[int, ResolvedWatch] = {}
    for rule in rules:
        destinations: List[ResolvedDestination] = []
        for dest in rule.forward_to:
            try:
                entity = await client.get_entity(dest)
            except RPCError as err:
                raise SystemExit(
                    f"Failed to resolve forward target '{dest}': {err}"
                ) from err
            destinations.append(
                ResolvedDestination(
                    target=entity,
                    label=_identifier_label(dest, entity),
                )
            )

        resolved_destinations = tuple(destinations)
        if not resolved_destinations:
            continue

        for source in rule.sources:
            try:
                entity = await client.get_entity(source)
            except RPCError as err:
                raise SystemExit(
                    f"Failed to resolve source chat '{source}': {err}"
                ) from err

            try:
                peer_id = get_peer_id(entity)
            except ValueError as err:
                raise SystemExit(
                    f"Could not derive peer ID for source '{source}': {err}"
                ) from err

            if peer_id in watch_map:
                raise SystemExit(
                    f"Duplicate watch rule for chat ID {peer_id}"
                )

            watch_map[peer_id] = ResolvedWatch(
                rule=rule,
                destinations=resolved_destinations,
                label=_identifier_label(source, entity),
            )
    return watch_map


def register_forward_handler(
    client: TelegramClient, watch_map: Dict[int, ResolvedWatch]
) -> None:
    @client.on(events.NewMessage)
    async def _(event: events.NewMessage.Event) -> None:
        if event.out:
            return

        peer_id = None
        if event.message is not None and event.message.peer_id is not None:
            try:
                peer_id = get_peer_id(event.message.peer_id)
            except ValueError:
                peer_id = None
        if peer_id is None:
            return

        watch = watch_map.get(peer_id)
        if watch is None:
            return

        message = event.message
        if (
            not watch.rule.include_service_messages
            and getattr(message, "action", None) is not None
        ):
            return

        for destination in watch.destinations:
            try:
                await client.forward_messages(destination.target, message)
            except RPCError as err:
                LOGGER.error(
                    "Failed to forward message %s from %s to %s: %s",
                    message.id,
                    watch.label,
                    destination.label,
                    err,
                )


async def run(config_path: pathlib.Path) -> None:
    config = load_config(config_path)
    client = TelegramClient(config.session, config.api_id, config.api_hash)

    await client.connect()
    if not await client.is_user_authorized():
        raise SystemExit(
            "Session is not authorized. Generate a valid session_string using Telethon."
        )

    watch_map = await resolve_watch_rules(client, config.watch_rules)
    if not watch_map:
        raise SystemExit("No valid watch rules available after resolution")

    register_forward_handler(client, watch_map)

    sources = [
        f"{resolved.label} ({peer_id})" for peer_id, resolved in watch_map.items()
    ]
    LOGGER.info("Monitoring sources: %s", ", ".join(sources))

    try:
        await client.run_until_disconnected()
    finally:
        await client.disconnect()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    try:
        asyncio.run(run(args.config))
    except KeyboardInterrupt:
        LOGGER.info("Shutting down on keyboard interrupt")


if __name__ == "__main__":
    main()
