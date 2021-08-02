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

from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantsBots, ChannelParticipantsRecent, ChannelParticipantsSearch

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


async def dellist(filename, channel):
    with open(filename, 'rt') as fp:
        reader = csv.reader(fp)
        for user_id, first_name in reader:
            client.kick_participant(channel, user_id)


async def gen_list(filename, channel):
    """
    docstring
    """
    limit = 200
    offset = 0
    last_users = set()
    with open(filename, 'wt', newline='') as fp:
        writer = csv.writer(fp)
        while True:
            result = await client(GetParticipantsRequest(
                channel=channel,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit,
                hash=0
            ))

            if not result.participants or len(result.participants)==0:
                print("No more participants found.")
                break

            for p, u in zip(result.participants, result.users):
                if isinstance(p, ChannelParticipantCreator):
                    continue
                # if not within_attack_times(p):
                #     continue
                writer.writerow((p.user_id, u.first_name))
            offset += len(result.participants)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--genlist", help='Generate CSV file containing list of users to be kicked')
    parser.add_argument(
        "--dellist", help='Kick users from the given CSV file.')
    options = parser.parse_args()
    me = await client.get_me()
    added = 0

    async for dialog in client.iter_dialogs():
        if not dialog.is_channel:
            continue

        channel_name = dialog.name

        if not channel_name == config['channel_name']:
            continue

        if options.genlist:
            await gen_list(options.genlist, dialog)
        if options.dellist:
            await dellist(options.dellist, dialog)


with client:
    client.loop.run_until_complete(main())
