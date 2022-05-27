import os
import logging
import random
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import ADMINS, LOG_CHANNEL, FILE_CAPTION, TARGET_CHANNEL, get_size
from database.connections_mdb import active_connection
import re
import json
import base64
logger = logging.getLogger(__name__)

INDEX_FILES = {}

IMAGE = ["https://te.legra.ph/file/f58032b4b41f5335e0a33.jpg"]

@Client.on_message(filters.command("start") & filters.incoming & ~filters.edited)
async def start(bot, message):
    if message.chat.type in ['group', 'supergroup']:
        await message.reply("""I don't work in Gorups or Channels.""")
        if not await db.get_chat(message.chat.id):
            total=await bot.get_chat_members_count(message.chat.id)
            await bot.send_message(LOG_CHANNEL, "#NewChat")       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await bot.send_message(LOG_CHANNEL, "#NewUser")
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('⚡️ Main Channel ⚡️', url='https://t.me/KCFilmss'),
            InlineKeyboardButton('🔰 Main Group 🔰', url='https://t.me/KC_Films')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(IMAGE),
            caption="""Hello I am a Auto Forward Bot devoloped by @kcfilmss, I can forward files from a Public/Private Channel to a Public/Private Group/Channel.""",
            reply_markup=reply_markup,
            parse_mode='html'
        )
        return

    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('⚡️ Main Channel ⚡️', url='https://t.me/KCFilmss'),
            InlineKeyboardButton('🔰 Main Group 🔰', url='https://t.me/KC_Films')
            ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(IMAGE),
            caption="""Hello I am a Auto Forward Bot devoloped by @kcfilmss, I can forward files from a Public/Private Channel to a Public/Private Group/Channel.""",
            reply_markup=reply_markup,
            parse_mode='html'
        )
        return
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("🙂 I am sending files in your TARGET CHANNEL, when it will complete i will notify you via a message. If i am not sending files in your TARGET CHANNEL then check your logs.")
        file_id = data.split("-", 1)[1]
        msgs = INDEX_FILES.get(file_id)
        frwded = 0
        pling = 0
        if not msgs:
            file = await bot.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await bot.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            INDEX_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if FILE_CAPTION:
                try:
                    f_caption=FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption='@KCFilmss'
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await bot.send_cached_media(
                    chat_id=TARGET_CHANNEL,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
                frwded += 1
                pling += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await bot.send_cached_media(
                    chat_id=TARGET_CHANNEL,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    )
                frwded += 1
                pling += 1
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            if pling == 1:
                await sts.edit_text(f"Forwarded:- <code>{frwded}</code>")
                pling -= 1
            await asyncio.sleep(3)
        await sts.delete()
        await bot.send_message(
            chat_id=message.chat.id,
            text=f"😎 All files have been successfully sent to TARGET CHANNEL, If not sent check your logs.\n\nTotal Files:- sO0N\nForwarded:- <code>{frwded}</code>"
            )
        return
