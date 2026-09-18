from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(slots=True)
class User:
    raw: Dict[str, Any]

    @property
    def id(self): return self.raw.get("id")
    @property
    def is_bot(self): return self.raw.get("is_bot", False)
    @property
    def username(self): return self.raw.get("username")
    @property
    def first_name(self): return self.raw.get("first_name", "")
    @property
    def last_name(self): return self.raw.get("last_name", "")
    @property
    def full_name(self): return " ".join(x for x in (self.first_name, self.last_name) if x)


@dataclass(slots=True)
class Chat:
    raw: Dict[str, Any]

    @property
    def id(self): return self.raw.get("id")
    @property
    def type(self): return self.raw.get("type")
    @property
    def title(self): return self.raw.get("title")
    @property
    def username(self): return self.raw.get("username")
    @property
    def description(self): return self.raw.get("description")


class Message:
    def __init__(self, bot, raw: Dict[str, Any]):
        self.bot = bot
        self.raw = raw or {}

    def __getitem__(self, key): return self.raw[key]
    def get(self, key, default=None): return self.raw.get(key, default)
    def __contains__(self, key): return key in self.raw
    @property
    def id(self): return self.raw.get("message_id")
    @property
    def message_id(self): return self.id
    @property
    def text(self): return self.raw.get("text") or self.raw.get("caption") or ""
    @property
    def caption(self): return self.raw.get("caption", "")
    @property
    def chat(self): return Chat(self.raw.get("chat") or {})
    @property
    def chat_id(self): return self.chat.id
    @property
    def from_user(self): return User(self.raw.get("from") or {})
    @property
    def user(self): return self.from_user
    @property
    def user_id(self): return self.from_user.id
    @property
    def date(self): return self.raw.get("date")
    @property
    def reply_to_message(self):
        raw = self.raw.get("reply_to_message")
        return Message(self.bot, raw) if isinstance(raw, dict) else None
    @property
    def photo(self): return self.raw.get("photo") or []
    @property
    def document(self): return self.raw.get("document")
    @property
    def audio(self): return self.raw.get("audio")
    @property
    def video(self): return self.raw.get("video")
    @property
    def animation(self): return self.raw.get("animation")
    @property
    def voice(self): return self.raw.get("voice")
    @property
    def video_note(self): return self.raw.get("video_note")
    @property
    def sticker(self): return self.raw.get("sticker")
    @property
    def location(self): return self.raw.get("location")
    @property
    def contact(self): return self.raw.get("contact")
    @property
    def venue(self): return self.raw.get("venue")
    @property
    def entities(self): return self.raw.get("entities") or []
    @property
    def reply_user_id(self): return self.reply_to_message.user_id if self.reply_to_message else None
    @property
    def target_user_id(self): return self.reply_user_id or self.user_id
    async def answer(self, text, **kwargs): return await self.bot.send_message(self.chat_id, text, **kwargs)
    async def reply(self, text, **kwargs): return await self.bot.send_message(self.chat_id, text, reply_to_message_id=self.id, **kwargs)
    async def edit(self, text, **kwargs): return await self.bot.edit_message_text(self.chat_id, self.id, text, **kwargs)
    async def delete(self): return await self.bot.delete_message(self.chat_id, self.id)
    async def pin(self, **kwargs): return await self.bot.pin_chat_message(self.chat_id, self.id, **kwargs)
    async def unpin(self, **kwargs): return await self.bot.unpin_chat_message(self.chat_id, self.id, **kwargs)
    async def ban(self, user_id=None, **kwargs): return await self.bot.ban_chat_member(self.chat_id, user_id or self.target_user_id, **kwargs)
    async def unban(self, user_id=None, **kwargs): return await self.bot.unban_chat_member(self.chat_id, user_id or self.target_user_id, **kwargs)
    async def mute(self, user_id=None, permissions=None, **kwargs): return await self.bot.restrict_chat_member(self.chat_id, user_id or self.target_user_id, permissions or {"can_send_messages": False}, **kwargs)
    async def unmute(self, user_id=None, permissions=None, **kwargs): return await self.bot.restrict_chat_member(self.chat_id, user_id or self.target_user_id, permissions or {"can_send_messages": True}, **kwargs)
    async def promote(self, user_id=None, **kwargs): return await self.bot.promote_chat_member(self.chat_id, user_id or self.target_user_id, **kwargs)


@dataclass(slots=True)
class CallbackQuery:
    bot: Any
    raw: Dict[str, Any]

    @property
    def id(self): return self.raw.get("id")
    @property
    def data(self): return self.raw.get("data")
    @property
    def from_user(self): return User(self.raw.get("from") or {})
    @property
    def message(self):
        raw = self.raw.get("message")
        return Message(self.bot, raw) if isinstance(raw, dict) else None
    async def answer(self, text=None, **kwargs): return await self.bot.answer_callback_query(self.id, text=text, **kwargs)


@dataclass(slots=True)
class Command:
    command: str
    args: str

    @property
    def args_list(self): return self.args.split() if self.args else []
