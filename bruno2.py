import csv
import argparse
from os import path, remove
from telethon import TelegramClient
from telethon.tl.functions import channels
import json
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantRequest, GetParticipantsRequest
from telethon import types
import pytz
from datetime import datetime

from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantsBots

with open("config.json", 'rt') as fp:
    config = json.loads(fp.read())

# Remember to use your own values from my.telegram.org!
api_id = config['api_id']
api_hash = config['api_hash']

client = TelegramClient('anon', api_id, api_hash)

PARIS_TZ = pytz.timezone(config['timezone'])


def within_attack_times(join_date):
    """
    docstring
    """
    attack_start1 = PARIS_TZ.localize(
        datetime.strptime("2021-07-30 22:45", "%Y-%m-%d %H:%M"))
    attack_end1 = PARIS_TZ.localize(
        datetime.strptime("2021-07-31 11:00", "%Y-%m-%d %H:%M"))

    attack_start2 = PARIS_TZ.localize(
        datetime.strptime("2021-08-02 09:00", "%Y-%m-%d %H:%M"))
    attack_end2 = PARIS_TZ.localize(
        datetime.strptime("2021-08-02 09:30", "%Y-%m-%d %H:%M"))

    within_attack1 = join_date.astimezone(
        PARIS_TZ) >= attack_start1 and join_date.astimezone(PARIS_TZ) <= attack_end1
    within_attack2 = join_date.astimezone(
        PARIS_TZ) >= attack_start2 and join_date.astimezone(PARIS_TZ) <= attack_end2

    return within_attack1 or within_attack2


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--genlist")
    parser.add_argument("--dellist")

    me = await client.get_me()
    print(f"Looking up Channel <{config['channel_name']}>...")
    async for dialog in client.iter_dialogs():
        if not dialog.is_channel:
            continue

        channel_name = dialog.name

        if not channel_name == config['channel_name']:
            continue

        print(f"Found Target Channel:{channel_name}")

        limit = 200
        offset = 0

        with open('./users.csv', 'wt', newline='') as fp:
            writer = csv.writer(fp)
            while True:
                users = await client.iter_participants(dialog, limit=limit, offset=offset)
                if len(users) <= 0:
                    break

                for user in users:
                    if isinstance(user.participant, ChannelParticipantCreator):
                        continue
                    participant = user.participant
                    if not within_attack_times(participant.date):
                        continue
                    writer.writerow(
                        (user.id, f"{user.first_name} {user.last_name}", f"{user.username}"))

                offset = offset + len(users)

            offset = 0
            while True:
                bot_users = await client.iter_participants(dialog, limit=limit, offset=offset, filter=ChannelParticipantsBots())
                if len(bot_users) <= 0:
                    break

                for bot_user in bot_users:
                    if isinstance(bot_user.participant, ChannelParticipantCreator):
                        continue
                    participant = bot_user.participant
                    writer.writerow(
                        (bot_user.id, f"{bot_user.first_name} {bot_user.last_name}", f"{bot_user.username}"))

                offset = offset + len(bot_users)
with client:
    client.loop.run_until_complete(main())
