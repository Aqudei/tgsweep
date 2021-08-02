from os import remove
from telethon import TelegramClient
from telethon.tl.functions import channels
import json
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest
from telethon import types
import pytz
import argparse
from datetime import datetime
import logging

from telethon.tl.types import ChannelParticipantsBots

logging.basicConfig(filename='./app.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

with open("config.json", 'rt') as fp:
    config = json.loads(fp.read())

# Remember to use your own values from my.telegram.org!
api_id = config['api_id']
api_hash = config['api_hash']

client = TelegramClient('anon', api_id, api_hash)

PARIS_TZ = pytz.timezone(config['timezone'])


def with_attack_times(join_date):
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
    removed = 0
    me = await client.get_me()
    logger.info(f"Looking up Channel <{config['channel_name']}>...")
    test = config['test']
    async for dialog in client.iter_dialogs():
        channel_name = dialog.name
        if not channel_name.lower() == config['channel_name'].lower():
            continue

        logger.info(f"Found Target Channel:{channel_name}!")
        logger.info(f"Retrieving Participants list...")

        logger.info(f"Cleaning up suspected channel members...")
        async for participant in client.iter_participants(dialog):
            if not with_attack_times(participant.date):
                continue

            logger.info(
                f"Removing participant with id: <{participant.user_id}>")
            if not test:
                await client.kick_participant(dialog, participant.user_id)
            removed = removed + 1

        logger.info(f"Removing remaning bots...")
        async for participant in client.iter_participants(dialog, filter=ChannelParticipantsBots()):
            logger.info(
                f"Removing bot participant with id: <{participant.user_id}>")
            if not test:
                await client.kick_participant(dialog, participant.user_id)
            removed = removed + 1

        logger.info(
            f"Removed <{removed}> participants from channel <{channel_name}>")

with client:
    client.loop.run_until_complete(main())
