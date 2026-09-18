<div align="center">

<img src="https://drive.google.com/uc?export=view&id=1rzTZVGNXCo5buCXsHXIe_roK_ghrqWq-" width="180" alt="VoidBale Logo">

### Async • Token-Only • Bale Bot Framework

A modern asynchronous Python framework for building **Bale Messenger bots** with the Bale Bot API.

<p>
  <a href="https://pypi.org/project/voidbale/">PyPI</a>
  ·
  <a href="https://weblics.ir/voidbale">Documentation</a>
  ·
  <a href="https://github.com/Sepehrkarimi1390/voidbale">GitHub</a>
</p>

</div>

---

## ✨ About

**VoidBale** is a Python library for building Bale Messenger bots using the **Bale Bot API**.

It is designed with simplicity, performance, and an asynchronous architecture in mind, making it easier to build modern and scalable Bale bots with Python.

VoidBale focuses exclusively on **token-based bots** and provides a clean interface for working with the Bale Bot API.

---

## 🚀 Features

* ⚡ Fully asynchronous
* 🤖 Built for the Bale Bot API
* 🔐 Token-only architecture
* 🌐 Webhook support
* 🎯 Powerful filtering system
* ⌨️ Inline and Reply Keyboard support
* 📦 Media support
* 🔄 Retry and network error handling
* ⏱️ Built-in scheduler
* 🧩 Direct Bot API requests
* 🛠️ Simple and extensible architecture
* 🐍 Built with Python

---

## 🔐 Token-Only Architecture

VoidBale is entirely based on **Bot Tokens** and the **Bale Bot API**.

The library does not implement user-account functionality such as user authentication, phone login, QR login, user sessions, MTProto, or self-bot functionality.

Its purpose is simple:

> **Build and run Bale bots using the official bot-oriented API model.**

---

## ⚡ Async First

VoidBale is designed from the ground up around Python's asynchronous programming model.

This allows developers to take advantage of `asyncio` and build bots capable of handling multiple operations efficiently without blocking the main event loop.

---

## 🌐 Webhook Ready

VoidBale supports **Webhook-based bot updates**, making it suitable for applications that need to receive updates through an HTTP endpoint.

This makes the framework suitable for both local development and server-side deployments.

---

## 🎯 Developer Friendly

VoidBale aims to keep bot development straightforward while still providing the flexibility needed for larger projects.

Its architecture brings together handlers, filters, keyboards, media operations, scheduling, webhooks, and direct Bot API requests in a consistent interface.

---

## 📦 Installation

Install VoidBale directly from PyPI:

```bash
pip install voidbale