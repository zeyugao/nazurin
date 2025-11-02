#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import pathlib
from dataclasses import dataclass
from typing import Dict, Iterable, List, Union
from urllib.parse import urlparse

from aiogram import Bot, Dispatcher, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


LOGGER = logging.getLogger(__name__)


SERVICE_MESSAGE_ATTRIBUTES = (
    "new_chat_members",
    "left_chat_member",
    "new_chat_title",
    "new_chat_photo",
    "delete_chat_photo",
    "group_chat_created",
    "supergroup_chat_created",
    "channel_chat_created",
    "message_auto_delete_timer_changed",
    "pinned_message",
    "invoice",
    "successful_payment",
    "user_shared",
    "chat_shared",
    "connected_website",
    "write_access_allowed",
    "passport_data",
    "proximity_alert_triggered",
    "forum_topic_created",
    "forum_topic_closed",
    "forum_topic_reopened",
    "general_forum_topic_hidden",
    "general_forum_topic_unhidden",
    "giveaway_created",
    "giveaway",
    "giveaway_winners",
    "video_chat_started",
    "video_chat_ended",
    "video_chat_participants_invited",
    "video_chat_scheduled",
)


ChatIdentifier = Union[int, str]


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

    raise ValueError("chat identifier must be string or integer")


@dataclass(frozen=True)
class WatchRule:
    source: ChatIdentifier
    forward_to: List[ChatIdentifier]
    include_service_messages: bool = False

    @classmethod
    def from_dict(cls, data: Dict) -> "WatchRule":
        source_raw = (
            data.get("source")
            or data.get("source_chat_id")
            or data.get("source_chat")
        )
        if source_raw is None:
            raise ValueError("watch entry must include source or source_chat_id")
        try:
            source_identifier = _normalize_chat_identifier(source_raw)
        except ValueError as err:
            raise ValueError("invalid source chat identifier") from err

        forward_to_raw = data.get("forward_to")
        if not isinstance(forward_to_raw, Iterable) or isinstance(
            forward_to_raw, (str, bytes)
        ):
            raise ValueError("forward_to must be a list of chat identifiers")

        destinations: List[ChatIdentifier] = []
        for item in forward_to_raw:
            try:
                destinations.append(_normalize_chat_identifier(item))
            except ValueError as err:
                raise ValueError(
                    "forward_to must contain valid chat identifiers"
                ) from err

        include_service_messages = bool(data.get("include_service_messages", False))
        return cls(
            source=source_identifier,
            forward_to=destinations,
            include_service_messages=include_service_messages,
        )


def load_config(config_path: pathlib.Path) -> tuple[str, List[WatchRule], bool]:
    try:
        with config_path.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
    except FileNotFoundError as err:
        raise SystemExit(f"Config file not found: {config_path}") from err
    except json.JSONDecodeError as err:
        raise SystemExit(f"Failed to parse JSON config: {err}") from err

    bot_token = data.get("bot_token")
    if not bot_token or not isinstance(bot_token, str):
        raise SystemExit("bot_token must be provided in the config file")

    watch_entries = data.get("watch_list")
    if not isinstance(watch_entries, list) or not watch_entries:
        raise SystemExit("watch_list must be a non-empty list of watch rules")

    drop_pending_updates = bool(data.get("polling", {}).get("drop_pending_updates", True))

    rules = [WatchRule.from_dict(entry) for entry in watch_entries]
    return bot_token, rules, drop_pending_updates


async def resolve_watch_rules(bot: Bot, rules: Iterable[WatchRule]) -> Dict[int, WatchRule]:
    watch_map: Dict[int, WatchRule] = {}
    for rule in rules:
        source = rule.source
        if isinstance(source, int):
            chat_id = source
        else:
            try:
                chat = await bot.get_chat(source)
            except TelegramBadRequest as err:
                raise SystemExit(
                    f"Failed to resolve source chat '{source}': {err}"
                ) from err
            chat_id = chat.id
        if chat_id in watch_map:
            raise SystemExit(f"Duplicate watch rule for chat ID {chat_id}")
        watch_map[chat_id] = rule
    return watch_map


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram chat forwarder bot (aiogram)")
    parser.add_argument(
        "-c",
        "--config",
        type=pathlib.Path,
        default=pathlib.Path("config.json"),
        help="Path to the JSON configuration file",
    )
    return parser.parse_args()


def _is_service_message(message: Message) -> bool:
    return any(bool(getattr(message, attr, None)) for attr in SERVICE_MESSAGE_ATTRIBUTES)


async def process_message(message: Message, watch_map: Dict[int, WatchRule]) -> None:
    rule = watch_map.get(message.chat.id)
    if rule is None:
        return

    if message.is_automatic_forward:
        return

    if not rule.include_service_messages and _is_service_message(message):
        return

    for dest_chat_id in rule.forward_to:
        try:
            await message.forward(chat_id=dest_chat_id)
        except TelegramBadRequest as err:
            LOGGER.error(
                "Failed to forward message %s from chat %s to %s: %s",
                message.message_id,
                message.chat.id,
                dest_chat_id,
                err,
            )


async def run_bot(config_path: pathlib.Path) -> None:
    bot_token, rules, drop_pending_updates = load_config(config_path)
    bot = Bot(token=bot_token)
    watch_map = await resolve_watch_rules(bot, rules)
    dispatcher = Dispatcher()
    router = Router(name="forwarder")
    watch_ids = tuple(watch_map.keys())

    router.message.filter(F.chat.id.in_(watch_ids))
    router.channel_post.filter(F.chat.id.in_(watch_ids))

    @router.message()
    async def handle_message(message: Message) -> None:
        await process_message(message, watch_map)

    @router.channel_post()
    async def handle_channel_post(message: Message) -> None:
        await process_message(message, watch_map)

    dispatcher.include_router(router)

    await bot.delete_webhook(drop_pending_updates=drop_pending_updates)

    sources = []
    for chat_id in watch_ids:
        rule = watch_map[chat_id]
        if isinstance(rule.source, str):
            sources.append(f"{chat_id} ({rule.source})")
        else:
            sources.append(str(chat_id))

    LOGGER.info(
        "Starting forwarder for source chats: %s",
        ", ".join(sources),
    )
    await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
        level=logging.INFO,
    )
    try:
        asyncio.run(run_bot(args.config))
    except KeyboardInterrupt:
        LOGGER.info("Shutting down on keyboard interrupt")


if __name__ == "__main__":
    main()
