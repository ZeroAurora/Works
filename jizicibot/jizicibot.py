# SPDX-License-Identifier: GLWTPL

import asyncio
import logging
import threading
from os import getenv
from random import random
from time import sleep

import schedule
from aiocqhttp import CQHttp, Event, Message, MessageSegment

from config import ENABLED_GROUPS, HOST, PORT  # Edit config.py

logging.basicConfig(
    filename="jizicibot.log",
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)

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
            logger.info("怼人了！（{} -> 群号 {}）".format(str(reply), event.group_id))


async def twelve():
    logger.info("十二点了！")
    msg: Message = MessageSegment.image("f29b5c32ad65cdbd38f097e6b5e314d4.image")
    for group in ENABLED_GROUPS:
        await bot.send_group_msg(group_id=group, message=msg)
        logger.info("报时已发送至群号 {}".format(group))


def scheduler():
    schedule.every().minute.do(asyncio.run, twelve())
    while not exit_event.is_set():
        schedule.run_pending()
        sleep(1)


@bot.server_app.before_serving
def init():
    global exit_event
    exit_event = threading.Event()
    threading.Thread(target=scheduler).start()


@bot.server_app.after_serving
def cleanup():
    exit_event.set()


if __name__ == "__main__":
    if str(getenv("JIZICI_ENV")) == "PRODUCTION":
        import uvicorn
        uvicorn.run("__main__:bot.asgi", host=HOST, port=PORT)
    else:
        bot.run(host=HOST, port=PORT)
