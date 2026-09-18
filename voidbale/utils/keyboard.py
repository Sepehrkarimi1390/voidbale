from __future__ import annotations
from typing import Any

class InlineKeyboard:
    def __init__(self): self._buttons = []; self._sizes = []
    def button(self, text, url=None, callback_data=None, web_app=None, login_url=None, switch_inline_query=None, switch_inline_query_current_chat=None, copy_text=None, **kwargs):
        data = {"text": text}
        values = {"url": url, "callback_data": callback_data, "web_app": web_app, "login_url": login_url, "switch_inline_query": switch_inline_query, "switch_inline_query_current_chat": switch_inline_query_current_chat, "copy_text": copy_text}
        data.update({k:v for k,v in values.items() if v is not None})
        data.update(kwargs)
        self._buttons.append(data)
        return self
    def add(self, *buttons): self._buttons.extend(buttons); return self
    def row(self, *buttons): self._buttons.extend(buttons); return self
    def adjust(self, *sizes): self._sizes = list(sizes) or [1]; return self
    def build(self, *sizes):
        sizes = list(sizes) or self._sizes or [1]
        rows=[]; i=0; index=0
        while i < len(self._buttons):
            size=sizes[index % len(sizes)]
            rows.append(self._buttons[i:i+size]); i += size; index += 1
        return {"inline_keyboard": rows}
    def as_markup(self, *sizes): return self.build(*sizes)
    def __dict__(self): return self.build()

class ReplyKeyboard:
    def __init__(self, resize_keyboard=True, one_time_keyboard=False, selective=False):
        self._buttons=[]; self._sizes=[]; self.resize_keyboard=resize_keyboard; self.one_time_keyboard=one_time_keyboard; self.selective=selective
    def button(self, text, **kwargs):
        self._buttons.append({"text": text, **kwargs}); return self
    def add(self, *buttons): self._buttons.extend(buttons); return self
    def row(self, *buttons): self._buttons.extend(buttons); return self
    def adjust(self, *sizes): self._sizes=list(sizes) or [1]; return self
    def build(self, *sizes):
        sizes=list(sizes) or self._sizes or [1]
        rows=[]; i=0; index=0
        while i < len(self._buttons):
            size=sizes[index % len(sizes)]
            rows.append(self._buttons[i:i+size]); i += size; index += 1
        return {"keyboard": rows, "resize_keyboard": self.resize_keyboard, "one_time_keyboard": self.one_time_keyboard, "selective": self.selective}
    def as_markup(self, *sizes): return self.build(*sizes)

class ReplyKeyboardRemove:
    def __init__(self, selective=False): self.selective=selective
    def as_markup(self): return {"remove_keyboard": True, "selective": self.selective}

class ForceReply:
    def __init__(self, selective=False, input_field_placeholder=None):
        self.selective=selective; self.input_field_placeholder=input_field_placeholder
    def as_markup(self):
        data={"force_reply": True, "selective": self.selective}
        if self.input_field_placeholder is not None: data["input_field_placeholder"]=self.input_field_placeholder
        return data
