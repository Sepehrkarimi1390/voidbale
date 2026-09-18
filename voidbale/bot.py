from __future__ import annotations

import asyncio
import inspect
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp

from .errors import BaleAPIError, RequestError
from .filters import Filter
from .models import CallbackQuery, Message
from .scheduler import Scheduler


class Bot:
    def __init__(
        self,
        token: str,
        *,
        base_url="https://tapi.bale.ai/bot",
        request_timeout=45.0,
        max_retries=3,
        retry_delay=0.5,
        auto_reconnect=True,
    ):
        if not isinstance(token, str) or not token.strip():
            raise ValueError("A Bale bot token is required")
        self.token = token.strip()
        self.base_url = base_url.rstrip("/")
        self.request_timeout = float(request_timeout)
        self.max_retries = max(1, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self.auto_reconnect = bool(auto_reconnect)
        self.session: Optional[aiohttp.ClientSession] = None
        self.offset = 0
        self.running = False
        self.user = None
        self.scheduler = Scheduler()
        self.metrics = {"updates": 0, "messages": 0, "callbacks": 0, "requests": 0, "errors": 0}
        self._message_handlers = []
        self._callback_handlers = []
        self._update_handlers = []
        self._error_handlers = []
        self._waiters = []

    def _url(self, method: str) -> str:
        return f"{self.base_url}{self.token}/{method}"

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    def command(self, *names):
        wanted = {str(x).lstrip("/").lower() for x in names}
        return self.message(Filter(self._command_match_factory(wanted)))

    @staticmethod
    def _command_match_factory(wanted):
        def match(message):
            text = getattr(message, "text", "") or ""
            if not text.startswith("/"):
                return False
            command = text[1:].split(maxsplit=1)[0].split("@", 1)[0].lower()
            return command in wanted
        return match

    def message(self, *filters, **kwargs):
        if "filters" in kwargs:
            value = kwargs["filters"]
            filters += tuple(value if isinstance(value, (list, tuple)) else (value,))
        def decorator(fn):
            self._message_handlers.append((filters, fn))
            return fn
        return decorator

    def on_message(self, predicate=None):
        return self.message(*([predicate] if predicate else []))

    def text(self, value):
        return self.message(Filter(lambda m: (m.text or "").lower() == str(value).lower()))

    def callback_query(self, *filters):
        def decorator(fn):
            self._callback_handlers.append((filters, fn))
            return fn
        return decorator

    def on_update(self, fn):
        self._update_handlers.append(fn)
        return fn

    def on_error(self, fn):
        self._error_handlers.append(fn)
        return fn

    def wait_for(self, event="message", check=None, timeout=None):
        async def waiter():
            future = asyncio.get_running_loop().create_future()
            self._waiters.append((event, check, future))
            try:
                return await asyncio.wait_for(future, timeout)
            finally:
                self._waiters = [item for item in self._waiters if item[2] is not future]
        return waiter()

    async def start(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.request_timeout))
        return self

    async def close(self):
        self.running = False
        await self.scheduler.close()
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def request(self, method: str, **payload):
        if not isinstance(method, str) or not method.strip():
            raise ValueError("API method is required")
        await self.start()
        body = {key: value for key, value in payload.items() if value is not None}
        last = None
        for attempt in range(self.max_retries):
            try:
                self.metrics["requests"] += 1
                async with self.session.post(self._url(method), json=body) as response:
                    try:
                        data = await response.json(content_type=None)
                    except Exception as exc:
                        raise RequestError(f"Invalid Bale API response: {exc}") from exc
                    if response.status >= 400 or not data.get("ok", False):
                        desc = data.get("description", f"HTTP {response.status}")
                        if "Not Implemented" in desc:
                            raise NotImplementedError(desc)
                        raise BaleAPIError(desc, method, response.status, data.get("parameters"))
                    return data
            except (BaleAPIError, NotImplementedError):
                self.metrics["errors"] += 1
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError, RequestError) as exc:
                last = exc
                if attempt + 1 < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
        self.metrics["errors"] += 1
        raise last

    async def request_multipart(self, method, fields=None, files=None):
        await self.start()
        fields = fields or {}
        files = files or {}
        last = None
        for attempt in range(self.max_retries):
            opened = []
            try:
                form = aiohttp.FormData()
                for key, value in fields.items():
                    if value is not None:
                        form.add_field(key, str(value))
                for key, value in files.items():
                    if isinstance(value, (str, os.PathLike)) and Path(value).exists():
                        fp = open(value, "rb")
                        opened.append(fp)
                        form.add_field(key, fp, filename=Path(value).name)
                    elif isinstance(value, tuple) and len(value) >= 2:
                        content, filename = value[:2]
                        content_type = value[2] if len(value) > 2 else None
                        form.add_field(key, content, filename=filename, content_type=content_type)
                    else:
                        form.add_field(key, value)
                self.metrics["requests"] += 1
                async with self.session.post(self._url(method), data=form) as response:
                    try:
                        data = await response.json(content_type=None)
                    except Exception as exc:
                        raise RequestError(f"Invalid Bale API response: {exc}") from exc
                    if response.status >= 400 or not data.get("ok", False):
                        desc = data.get("description", f"HTTP {response.status}")
                        if "Not Implemented" in desc:
                            raise NotImplementedError(desc)
                        raise BaleAPIError(desc, method, response.status, data.get("parameters"))
                    return data
            except (BaleAPIError, NotImplementedError):
                self.metrics["errors"] += 1
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError, RequestError) as exc:
                last = exc
                if attempt + 1 < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
            finally:
                for fp in opened:
                    fp.close()
        self.metrics["errors"] += 1
        raise last

    async def get_me(self):
        result = (await self.request("getMe")).get("result", {})
        self.user = result
        return result

    async def get_updates(self, timeout=30, limit=100, allowed_updates=None):
        payload = {"offset": self.offset, "timeout": timeout, "limit": limit}
        if allowed_updates is not None:
            payload["allowed_updates"] = list(allowed_updates)
        return (await self.request("getUpdates", **payload)).get("result", [])

    async def process_update(self, update):
        self.metrics["updates"] += 1
        for fn in list(self._update_handlers):
            await self._call(fn, update)
        await self._resolve_waiters("update", update)
        raw_message = update.get("message") or update.get("edited_message") or update.get("channel_post") or update.get("edited_channel_post")
        if isinstance(raw_message, dict):
            self.metrics["messages"] += 1
            message = Message(self, raw_message)
            await self._resolve_waiters("message", message)
            await self._dispatch_message(message)
        raw_callback = update.get("callback_query")
        if isinstance(raw_callback, dict):
            self.metrics["callbacks"] += 1
            query = CallbackQuery(self, raw_callback)
            await self._resolve_waiters("callback_query", query)
            await self._dispatch_callback(query)
        return update

    async def _resolve_waiters(self, event, value):
        for event_name, check, future in list(self._waiters):
            if event_name != event or future.done():
                continue
            try:
                matched = True if check is None else bool(await check(value) if inspect.iscoroutinefunction(check) else check(value))
            except Exception:
                matched = False
            if matched:
                future.set_result(value)

    async def _match(self, filters, value):
        for item in filters:
            if item is None:
                continue
            result = await item(value) if inspect.iscoroutinefunction(item) else item(value)
            if not result:
                return False
        return True

    async def _call(self, fn, *values):
        signature = inspect.signature(fn)
        try:
            signature.bind(*values)
            return await fn(*values)
        except TypeError:
            raw_values = [value.raw if hasattr(value, "raw") else value for value in values]
            signature.bind(*raw_values)
            return await fn(*raw_values)

    async def _dispatch_message(self, message):
        for filters, fn in list(self._message_handlers):
            try:
                if await self._match(filters, message):
                    await self._call(fn, message)
            except Exception as exc:
                await self._handle_error(exc, message)

    async def _dispatch_callback(self, query):
        for filters, fn in list(self._callback_handlers):
            try:
                if await self._match(filters, query):
                    await self._call(fn, query)
            except Exception as exc:
                await self._handle_error(exc, query)

    async def _handle_error(self, error, event):
        self.metrics["errors"] += 1
        if not self._error_handlers:
            raise error
        for fn in list(self._error_handlers):
            await self._call(fn, error, event)

    async def poll(self, *, timeout=30, limit=100, allowed_updates=None):
        await self.start()
        self.running = True
        while self.running:
            try:
                updates = await self.get_updates(timeout=timeout, limit=limit, allowed_updates=allowed_updates)
                for update in updates:
                    if "update_id" in update:
                        self.offset = max(self.offset, int(update["update_id"]) + 1)
                    await self.process_update(update)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                try:
                    await self._handle_error(exc, None)
                except Exception:
                    if not self.auto_reconnect:
                        raise
                if self.auto_reconnect:
                    await asyncio.sleep(self.retry_delay)
                else:
                    raise
        return self

    async def start_polling(self, **kwargs):
        return await self.poll(**kwargs)

    def run(self, **kwargs):
        try:
            asyncio.run(self.poll(**kwargs))
        except KeyboardInterrupt:
            pass

    async def set_webhook(self, url, **kwargs):
        return (await self.request("setWebhook", url=url, **kwargs)).get("result")

    async def delete_webhook(self, **kwargs):
        return (await self.request("deleteWebhook", **kwargs)).get("result")

    async def get_webhook_info(self):
        return (await self.request("getWebhookInfo")).get("result", {})

    def run_webhook(self, url, *, host="0.0.0.0", port=8080, path="/webhook", secret_token=None, **kwargs):
        from .webhook import WebhookServer
        async def runner():
            await self.set_webhook(url, **kwargs)
            await self.start()
            server = WebhookServer(self, path=path, secret_token=secret_token)
            await server.start_async(host, port)
        asyncio.run(runner())

    async def _send(self, method, chat_id, **kwargs):
        if chat_id is None or (isinstance(chat_id, str) and not chat_id.strip()):
            raise BaleAPIError("chat_id cannot be empty")
        return (await self.request(method, chat_id=str(chat_id), **kwargs)).get("result")

    async def send_message(self, chat_id, text, **kwargs):
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = self._markup(kwargs["reply_markup"])
        result = (await self.request("sendMessage", chat_id=str(chat_id), text=text, **kwargs)).get("result", {})
        return Message(self, result) if isinstance(result, dict) else result

    async def edit_message_text(self, chat_id, message_id, text, **kwargs):
        if "reply_markup" in kwargs:
            kwargs["reply_markup"] = self._markup(kwargs["reply_markup"])
        result = (await self.request("editMessageText", chat_id=str(chat_id), message_id=message_id, text=text, **kwargs)).get("result", {})
        return Message(self, result) if isinstance(result, dict) else result

    async def edit_message_caption(self, chat_id, message_id, caption, **kwargs):
        return (await self.request("editMessageCaption", chat_id=str(chat_id), message_id=message_id, caption=caption, **kwargs)).get("result")

    async def edit_message_reply_markup(self, chat_id, message_id, reply_markup, **kwargs):
        return (await self.request("editMessageReplyMarkup", chat_id=str(chat_id), message_id=message_id, reply_markup=self._markup(reply_markup), **kwargs)).get("result")

    async def delete_message(self, chat_id, message_id):
        return (await self.request("deleteMessage", chat_id=str(chat_id), message_id=message_id)).get("result")

    async def forward_message(self, chat_id, from_chat_id, message_id, **kwargs):
        return (await self.request("forwardMessage", chat_id=str(chat_id), from_chat_id=str(from_chat_id), message_id=message_id, **kwargs)).get("result")

    async def copy_message(self, chat_id, from_chat_id, message_id, **kwargs):
        return (await self.request("copyMessage", chat_id=str(chat_id), from_chat_id=str(from_chat_id), message_id=message_id, **kwargs)).get("result")

    async def send_photo(self, chat_id, photo, **kwargs):
        return await self._media("sendPhoto", "photo", chat_id, photo, **kwargs)

    async def send_document(self, chat_id, document, **kwargs):
        return await self._media("sendDocument", "document", chat_id, document, **kwargs)

    async def send_audio(self, chat_id, audio, **kwargs):
        return await self._media("sendAudio", "audio", chat_id, audio, **kwargs)

    async def send_video(self, chat_id, video, **kwargs):
        return await self._media("sendVideo", "video", chat_id, video, **kwargs)

    async def send_animation(self, chat_id, animation, **kwargs):
        return await self._media("sendAnimation", "animation", chat_id, animation, **kwargs)

    async def send_voice(self, chat_id, voice, **kwargs):
        return await self._media("sendVoice", "voice", chat_id, voice, **kwargs)

    async def send_video_note(self, chat_id, video_note, **kwargs):
        return await self._media("sendVideoNote", "video_note", chat_id, video_note, **kwargs)

    async def send_sticker(self, chat_id, sticker, **kwargs):
        return await self._media("sendSticker", "sticker", chat_id, sticker, **kwargs)

    async def _media(self, method, field, chat_id, value, **kwargs):
        cid = str(chat_id)
        if isinstance(value, (str, os.PathLike)) and Path(value).exists():
            return (await self.request_multipart(method, {"chat_id": cid, **kwargs}, {field: value})).get("result")
        return (await self.request(method, chat_id=cid, **{field: value}, **kwargs)).get("result")

    async def send_location(self, chat_id, latitude, longitude, **kwargs):
        return await self._send("sendLocation", chat_id, latitude=latitude, longitude=longitude, **kwargs)

    async def send_contact(self, chat_id, phone_number, first_name, **kwargs):
        return await self._send("sendContact", chat_id, phone_number=phone_number, first_name=first_name, **kwargs)

    async def send_venue(self, chat_id, latitude, longitude, title, address, **kwargs):
        raise NotImplementedError("sendVenue is not implemented on Bale API server.")

    async def send_media_group(self, chat_id, media, **kwargs):
        return await self._send("sendMediaGroup", chat_id, media=list(media), **kwargs)

    async def send_chat_action(self, chat_id, action):
        if chat_id is None or (isinstance(chat_id, str) and not chat_id.strip()):
            raise BaleAPIError("chat_id cannot be empty")
        if not action:
            raise ValueError("action is required")
        return await self._send("sendChatAction", chat_id, action=action)

    async def answer_callback_query(self, callback_query_id, text=None, **kwargs):
        data = {"callback_query_id": callback_query_id, **kwargs}
        if text is not None:
            data["text"] = text
        return (await self.request("answerCallbackQuery", **data)).get("result")

    async def get_chat(self, chat_id):
        return (await self.request("getChat", chat_id=str(chat_id))).get("result", {})

    async def get_chat_member(self, chat_id, user_id):
        return (await self.request("getChatMember", chat_id=str(chat_id), user_id=user_id)).get("result", {})

    async def get_chat_administrators(self, chat_id):
        return (await self.request("getChatAdministrators", chat_id=str(chat_id))).get("result", [])

    async def get_chat_member_count(self, chat_id):
        result = await self.request("getChatMemberCount", chat_id=str(chat_id))
        return result.get("result")

    async def leave_chat(self, chat_id):
        return await self._send("leaveChat", chat_id)

    async def set_chat_title(self, chat_id, title):
        return await self._send("setChatTitle", chat_id, title=title)

    async def set_chat_description(self, chat_id, description=""):
        return await self._send("setChatDescription", chat_id, description=description)

    async def set_chat_photo(self, chat_id, photo, **kwargs):
        return await self._media("setChatPhoto", "photo", chat_id, photo, **kwargs)

    async def delete_chat_photo(self, chat_id):
        return await self._send("deleteChatPhoto", chat_id)

    async def pin_chat_message(self, chat_id, message_id, **kwargs):
        return await self._send("pinChatMessage", chat_id, message_id=message_id, **kwargs)

    async def unpin_chat_message(self, chat_id, message_id=None, **kwargs):
        if chat_id is None or (isinstance(chat_id, str) and not chat_id.strip()):
            raise BaleAPIError("chat_id cannot be empty")
        return await self._send("unpinChatMessage", chat_id, message_id=message_id, **kwargs)

                                                                         
                                                             
                                                               

    def _markup(self, markup):
        """تبدیل InlineKeyboard به dict قابل ارسال به API."""
        if markup is None:
            return None
        if isinstance(markup, dict):
            return markup
        if hasattr(markup, "build"):
            return markup.build()
        return markup

    async def get_file(self, file_id):
        if not isinstance(file_id, str) or not file_id.strip():
            raise BaleAPIError("file_id cannot be empty")
        result = (await self.request("getFile", file_id=file_id)).get("result", {})
        if not result:
            raise BaleAPIError("File not found")
        return result

    async def set_chat_permissions(self, chat_id, permissions):
        raise NotImplementedError("setChatPermissions is not implemented on Bale API server.")
