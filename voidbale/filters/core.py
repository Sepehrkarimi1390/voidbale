from __future__ import annotations
import re

class Filter:
    def __call__(self, value): return True
    def __and__(self, other):
        return Filter(lambda value: self(value) and other(value))
    def __or__(self, other):
        return Filter(lambda value: self(value) or other(value))
    def __invert__(self):
        return Filter(lambda value: not self(value))
    def __init__(self, fn=None): self.fn = fn or (lambda value: True)
    def __call__(self, value): return bool(self.fn(value))

class _F:
    def __getattr__(self, name):
        return Field(name)

class Field:
    def __init__(self, name): self.name = name
    def __eq__(self, value): return Filter(lambda obj: _get(obj, self.name) == value)
    def __ne__(self, value): return Filter(lambda obj: _get(obj, self.name) != value)
    def __contains__(self, value): return Filter(lambda obj: value in (_get(obj, self.name) or ""))
    def matches(self, pattern, flags=0): 
        rx = re.compile(pattern, flags)
        return Filter(lambda obj: bool(rx.search(str(_get(obj, self.name) or ""))))
    def startswith(self, value): return Filter(lambda obj: str(_get(obj, self.name) or "").startswith(value))
    def endswith(self, value): return Filter(lambda obj: str(_get(obj, self.name) or "").endswith(value))

def _get(obj, path):
    value = obj
    for part in path.split("."):
        if isinstance(value, dict): value = value.get(part)
        else: value = getattr(value, part, None)
    return value

def text(value=None):
    return Filter(lambda m: m.text == value if value is not None else bool(m.text))

def command(*names):
    normalized = {x.lstrip("/").lower() for x in names}
    def check(m):
        text = getattr(m, "text", "").strip()
        if not text.startswith("/"): return False
        cmd = text[1:].split(maxsplit=1)[0].split("@", 1)[0].lower()
        return cmd in normalized
    return Filter(check)

def regexp(pattern, flags=0):
    rx = re.compile(pattern, flags)
    return Filter(lambda m: bool(rx.search(getattr(m, "text", "") or "")))

def chat_type(value):
    return Filter(lambda m: getattr(getattr(m, "chat", None), "type", None) == value)

F = _F()
