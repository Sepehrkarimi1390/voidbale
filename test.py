import asyncio
import traceback
from unittest.mock import AsyncMock, patch

from voidbale import Bot, InlineKeyboard
from voidbale.errors import BaleAPIError


                                                           
                                  
                                                           
BOT_TOKEN = "717204939:kZ2pgkeQHaDJcVN8xuCe2G1rhJe59McFsYs"


                                                           
                                                         
                                                           
async def test_get_me(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"id": 1, "is_bot": True, "username": "test_bot"}}
        user = await bot.get_me()
        assert user["id"] == 1
        assert user["username"] == "test_bot"
        mock_req.assert_called_once_with("getMe")


async def test_get_chat(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"id": 100, "type": "private", "title": "Test Chat"}}
        chat = await bot.get_chat(100)
        assert chat["id"] == 100
        mock_req.assert_called_once_with("getChat", chat_id="100")


async def test_get_chat_administrators(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": [{"user": {"id": 1}}]}
        admins = await bot.get_chat_administrators(100)
        assert len(admins) == 1
        mock_req.assert_called_once_with("getChatAdministrators", chat_id="100")


async def test_send_message(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"message_id": 10, "text": "Hello", "chat": {"id": 100}}}
        msg = await bot.send_message(100, "Hello")
        assert msg.id == 10
        assert msg.text == "Hello"
        mock_req.assert_called_once_with("sendMessage", chat_id="100", text="Hello")


async def test_reply(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"message_id": 11, "text": "Reply", "chat": {"id": 100}}}
        from voidbale import Message
        original_msg = Message(bot, {"message_id": 10, "chat": {"id": 100}})
        replied = await original_msg.reply("Reply")
        assert replied.id == 11
        mock_req.assert_called_once_with("sendMessage", chat_id="100", text="Reply", reply_to_message_id=10)


async def test_edit_message_text(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"message_id": 10, "text": "Edited"}}
        msg = await bot.edit_message_text(100, 10, "Edited")
        assert msg.text == "Edited"
        mock_req.assert_called_once_with("editMessageText", chat_id="100", message_id=10, text="Edited")


async def test_delete_message(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": True}
        res = await bot.delete_message(100, 10)
        assert res is True
        mock_req.assert_called_once_with("deleteMessage", chat_id="100", message_id=10)


async def test_forward_message(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"message_id": 12}}
        res = await bot.forward_message(200, 100, 10)
        assert res["message_id"] == 12
        mock_req.assert_called_once_with("forwardMessage", chat_id="200", from_chat_id="100", message_id=10)


async def test_copy_message(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"message_id": 13}}
        res = await bot.copy_message(200, 100, 10)
        assert res["message_id"] == 13
        mock_req.assert_called_once_with("copyMessage", chat_id="200", from_chat_id="100", message_id=10)


async def test_send_chat_action(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": True}
        res = await bot.send_chat_action(100, "typing")
        assert res is True
        mock_req.assert_called_once_with("sendChatAction", chat_id="100", action="typing")

    try:
        await bot.send_chat_action("", "typing")
        raise AssertionError("BaleAPIError انتظار می‌رفت")
    except BaleAPIError:
        pass


async def test_send_location(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"location": {"latitude": 35.6, "longitude": 51.4}}}
        res = await bot.send_location(100, 35.6, 51.4)
        assert res["location"]["latitude"] == 35.6
        mock_req.assert_called_once_with("sendLocation", chat_id="100", latitude=35.6, longitude=51.4)


async def test_send_contact(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"contact": {"phone_number": "09120000000"}}}
        res = await bot.send_contact(100, "09120000000", "John")
        assert res["contact"]["phone_number"] == "09120000000"
        mock_req.assert_called_once_with("sendContact", chat_id="100", phone_number="09120000000", first_name="John")


async def test_send_venue(bot):
    try:
        await bot.send_venue(100, 35.6, 51.4, "Place", "Address")
        raise AssertionError("NotImplementedError انتظار می‌رفت")
    except NotImplementedError:
        pass


async def test_keyboard(bot):
    kb = InlineKeyboard().button("Click", callback_data="btn").build()
    assert kb == {"inline_keyboard": [[{"text": "Click", "callback_data": "btn"}]]}


async def test_pin_chat_message(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": True}
        res = await bot.pin_chat_message(100, 10)
        assert res is True
        mock_req.assert_called_once_with("pinChatMessage", chat_id="100", message_id=10)


async def test_unpin_chat_message(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": True}
        res = await bot.unpin_chat_message(100, 10)
        assert res is True
        mock_req.assert_called_once_with("unpinChatMessage", chat_id="100", message_id=10)

    try:
        await bot.unpin_chat_message("")
        raise AssertionError("BaleAPIError انتظار می‌رفت")
    except BaleAPIError:
        pass


async def test_set_chat_permissions(bot):
    try:
        await bot.set_chat_permissions(100, {"can_send_messages": False})
        raise AssertionError("NotImplementedError انتظار می‌رفت")
    except NotImplementedError:
        pass


async def test_get_webhook_info(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"url": "https://example.com/webhook"}}
        info = await bot.get_webhook_info()
        assert info["url"] == "https://example.com/webhook"
        mock_req.assert_called_once_with("getWebhookInfo")


async def test_get_file_error_handling(bot):
    try:
        await bot.get_file("")
        raise AssertionError("BaleAPIError انتظار می‌رفت")
    except BaleAPIError:
        pass

    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {}}
        try:
            await bot.get_file("invalid_file_id")
            raise AssertionError("BaleAPIError انتظار می‌رفت")
        except BaleAPIError:
            pass

    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"file_id": "123", "file_path": "photos/1.jpg"}}
        res = await bot.get_file("valid_id")
        assert res["file_path"] == "photos/1.jpg"


async def test_raw_bot_api_request(bot):
    with patch.object(bot, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"ok": True, "result": {"custom": "data"}}
        res = await bot.request("customMethod", param="value")
        assert res == {"ok": True, "result": {"custom": "data"}}
        mock_req.assert_called_once_with("customMethod", param="value")


                                                           
                 
                                                           
ALL_TESTS = [
    ("test_get_me", test_get_me),
    ("test_get_chat", test_get_chat),
    ("test_get_chat_administrators", test_get_chat_administrators),
    ("test_send_message", test_send_message),
    ("test_reply", test_reply),
    ("test_edit_message_text", test_edit_message_text),
    ("test_delete_message", test_delete_message),
    ("test_forward_message", test_forward_message),
    ("test_copy_message", test_copy_message),
    ("test_send_chat_action", test_send_chat_action),
    ("test_send_location", test_send_location),
    ("test_send_contact", test_send_contact),
    ("test_send_venue", test_send_venue),
    ("test_keyboard", test_keyboard),
    ("test_pin_chat_message", test_pin_chat_message),
    ("test_unpin_chat_message", test_unpin_chat_message),
    ("test_set_chat_permissions", test_set_chat_permissions),
    ("test_get_webhook_info", test_get_webhook_info),
    ("test_get_file_error_handling", test_get_file_error_handling),
    ("test_raw_bot_api_request", test_raw_bot_api_request),
]


async def run_all_tests():
    """همه تست‌ها را اجرا می‌کند و خلاصه نتیجه را برمی‌گرداند."""
                                             
    test_bot = Bot("123456:TEST_TOKEN")
    passed = 0
    failed = 0
    lines = []

    for name, fn in ALL_TESTS:
        try:
            await fn(test_bot)
            passed += 1
            lines.append(f"✅ {name}")
        except Exception as exc:
            failed += 1
            short = f"{type(exc).__name__}: {exc}"
            lines.append(f"❌ {name}\n   ↳ {short}")

    try:
        await test_bot.close()
    except Exception:
        pass

    summary = (
        f"🧪 نتیجه اجرای تست‌ها\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ موفق: {passed}\n"
        f"❌ ناموفق: {failed}\n"
        f"📊 کل: {passed + failed}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(lines)
    )
    return summary


                                                           
          
                                                           
bot = Bot(BOT_TOKEN)


@bot.command("start")
async def cmd_start(message):
    await message.reply(
        "سلام! 👋\n"
        "برای اجرای همه تست‌های کتابخانه VoidBale، دستور /testall را بزنید."
    )


@bot.command("testall")
async def cmd_testall(message):
    await message.reply("⏳ در حال اجرای تست‌ها... لطفاً صبر کنید.")
    try:
        summary = await run_all_tests()
    except Exception as exc:
        summary = f"❌ خطا در اجرای تست‌ها:\n{type(exc).__name__}: {exc}\n\n{traceback.format_exc()}"

                                          
    max_len = 3500
    if len(summary) <= max_len:
        await message.reply(summary)
    else:
        for i in range(0, len(summary), max_len):
            await message.reply(summary[i:i + max_len])


if __name__ == "__main__":
    print("ربات تست‌ران شروع شد... (Ctrl+C برای توقف)")
    bot.run()
