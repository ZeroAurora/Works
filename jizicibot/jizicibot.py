# SPDX-License-Identifier: GLWTPL

import asyncio
import threading
from random import random
from time import sleep

import schedule
from aiocqhttp import CQHttp, Event, Message, MessageSegment

from config import ENABLED_GROUPS, HOST, PORT # Edit config.py

bot = CQHttp()

@bot.on_message("group")
async def argue(event: Event):
    if event.group_id in ENABLED_GROUPS:
        msg = Message(event.message).extract_plain_text()
        if random() <= 0.001:
            reply: Message = MessageSegment.at(event.user_id) + MessageSegment.text(
                "{}个头".format(msg[0])
            )
            await bot.send(event, reply)
            print("怼人了！")


async def twelve():
    print("十二点了！")
    msg: Message = MessageSegment.image("f29b5c32ad65cdbd38f097e6b5e314d4.image")
    for group in ENABLED_GROUPS:
        await bot.send_group_msg(group_id=group, message=msg)

def scheduler():
    schedule.every().day.at("00:00").do(asyncio.run, twelve())
    while not exit_event.is_set():
        schedule.run_pending()
        sleep(1)

def main():
    threading.Thread(target=scheduler).start()
    bot.run(host=HOST, port=PORT)

if __name__ == "__main__":
    try:
        exit_event = threading.Event()
        main()
    finally:
        exit_event.set()
