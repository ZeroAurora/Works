# SPDX-License-Identifier: GLWTPL

from datetime import datetime
import logging
import os
import random
import shutil
import sqlite3
import tempfile
import time
from configparser import ConfigParser
from pathlib import Path
from typing import List

import requests
import schedule
from O365 import Account


def db_init(location: str):
    db = sqlite3.connect(location)
    db.execute(
        "CREATE TABLE IF NOT EXISTS queue (id TEXT UNIQUE, ext TEXT, url TEXT, status INT)"
    )
    return db


def login_to_o365(id: str, secret: str):
    account = Account((id, secret))
    if account.authenticate(
        scopes=["basic", "onedrive_all", "mailbox", "calendar", "address_book"]
    ):
        return account
    else:
        raise Exception("Not authenticated.")


def fetch_mew_thoughts(token: str, topic: str) -> dict:
    resp = requests.get(
        "https://api.mew.fun/api/v1/topics/{}/thoughts".format(topic),
        headers={"Authorization": "Bearer {}".format(token)},
    )
    if resp.status_code == 200:
        logging.info("Fetched Mew Topic {}".format(topic))
        return resp.json()
    else:
        raise Exception("Failed to fetch mew posts.")


def parse_mew_thoughts(data: dict) -> List[dict]:
    """Parses mew thoughts to a list of urls to pictures."""
    media_list = []
    for entry in data["entries"]:
        media_ids = entry["media"]  # type: list
        for id in media_ids:
            logging.info("Parsed media " + id)
            media_list.append(data["objects"]["media"][id])
    return media_list


def fetch_media(media_list: List[dict], db: sqlite3.Connection):
    """Fetches media and store state to database"""
    path_list = []
    tempdir = tempfile.gettempdir() + "/" + random.randbytes(4).hex()
    os.mkdir(tempdir)

    logging.info("Filling the queue...")
    queue = []
    for media in media_list:
        id = media["id"]
        ext = media["type"].split("/")[1]  # a lazy way to get extension
        url = media["url"]

        status_row = db.execute("SELECT status FROM queue WHERE id=?", (id,)).fetchone()
        if status_row and status_row[0] == 1:
            logging.info("Skipped downloaded {}".format(id))
        elif status_row and status_row[0] == -2:
            logging.info("Skipped previous failure {}".format(id))
        elif url.find("audit_blocked_") != -1:
            logging.info("Skipped audited {}".format(id))
        else:
            queue.append((id, ext, url, 0))
            logging.info("Added to database {}".format(id))
    db.executemany("INSERT INTO queue VALUES (?, ?, ?, ?)", queue)

    logging.info("Starting and resuming downloads...")
    downloads = db.execute("SELECT * FROM queue WHERE status!=1;").fetchall()
    status_updates = []
    for item in downloads:
        id = item[0]
        ext = item[1]
        url = item[2]
        status = item[3]

        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                filename = "{id}.{ext}".format(id=id, ext=ext)
                path = Path(tempdir, filename)
                with open(path, "xb") as f:
                    f.write(resp.content)
                logging.info("Fetched {}".format(url))
                status_updates.append((1, id))
                path_list.append(path)
            else:
                raise Exception("Failed to download pic ".format(url))
        except Exception as e:
            logging.error(e)

            if status == 0:
                status_updates.append((-1, id))
                logging.error("{} failed. Will retry next time.".format(id))
            elif status == -1:
                status_updates.append((-2, id))
                logging.error("{} failed again! Won't retry.".format(id))

        db.executemany("UPDATE queue SET status=? WHERE id=?", status_updates)

    return path_list, tempdir


def onedrive_upload(account: Account, remote: str, path_list: List[Path]):
    folder = account.storage().get_default_drive().get_item_by_path(remote)
    for file in path_list:
        folder.upload_file(file)
        logging.info("Uploaded {}".format(file))


def cleanup(tempdir: tempfile.TemporaryDirectory):
    shutil.rmtree(tempdir)
    logging.info("Cleaned up")


def send_success(token: str, thought: str, log: str):
    try:
        requests.post(
            "https://api.mew.fun/api/v1/thoughts/{}/comments".format(thought),
            data={"content": log},
            headers={"Authorization": "Bearer {}".format(token)},
        )
    except:
        logging.error("Failed to send log")


def workflow(account: Account, config: ConfigParser):
    logging.info("Started job.")
    db = db_init(config["Locations"]["Database"])
    data = fetch_mew_thoughts(config["Mew"]["Token"], config["Mew"]["TopicID"])
    media_list = parse_mew_thoughts(data)
    (file_list, tempdir) = fetch_media(media_list, db)
    onedrive_upload(account, config["Locations"]["Remote"], file_list)
    cleanup(tempdir)
    db.commit()
    db.close()
    logging.info("Completed job!")
    send_success(
        config["Mew"]["Token"],
        config["Mew"]["FeedbackThoughtID"],
        "Success at " + str(datetime.now()),
    )


def random_request(account: Account):
    try:
        ops = [
            lambda: account.mailbox().get_folders(),
            lambda: account.mailbox().inbox_folder().get_messages(),
            lambda: account.mailbox().outbox_folder().get_messages(),
            lambda: account.mailbox().drafts_folder().get_messages(),
            lambda: account.address_book().get_contacts(),
            lambda: account.address_book().get_folders(),
            lambda: account.schedule().list_calendars(),
            lambda: account.schedule().get_default_calendar(),
        ]
        random.choice(ops)()
        logging.info("Sent random request")
    except Exception as e:
        logging.error("Failed to send random request.", e)


def main():
    logging.getLogger().setLevel(logging.INFO)
    config = ConfigParser()
    config.read("config.ini")

    account = login_to_o365(config["Client"]["ID"], config["Client"]["Secret"])

    workflow(account, config)
    random_request(account)
    schedule.every().hour.do(workflow, account=account, config=config)
    schedule.every().hour.do(random_request, account=account)
    while True:
        schedule.run_pending()
        time.sleep(5)


if __name__ == "__main__":
    main()
