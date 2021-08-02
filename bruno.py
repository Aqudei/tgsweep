from os import path, remove
from telethon import TelegramClient
from telethon.tl.functions import channels
import json
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.channels import GetFullChannelRequest, GetParticipantsRequest, GetParticipantRequest
from telethon import types
import pytz
import argparse
from datetime import datetime
import logging
import os

from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantsBots, ChannelParticipantsRecent

logging.basicConfig(filename='./app.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

if not os.path.isfile('config.json'):
    print("'config.json' was not found in the working directory. Please ask developer.")
    exit(1)

with open("config.json", 'rt') as fp:
    config = json.loads(fp.read())

# Remember to use your own values from my.telegram.org!
api_id = config['api_id']
api_hash = config['api_hash']
test = config['test']
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


async def delete_participants(channel, filter, check_join_date=False):
    """
    docstring
    """
    removed = 0
    while True:
        participants = await client(GetParticipantsRequest(
            channel=channel,
            filter=filter,
            offset=0,
            limit=200,
            hash=0
        ))

        if participants.count <= 1:
            if not hasattr(participants[0], 'date'):
                break

        for participant in participants.participants:
            if isinstance(participant, ChannelParticipantCreator):
                continue

            if check_join_date:
                if not within_attack_times(participant.date):
                    continue

            logger.info(
                f"Removing participant with id: <{participant.user_id}>")
            if not test:
                await client.kick_participant(channel, participant.user_id)
            removed = removed + 1

    return removed


async def main():
    removed = 0
    me = await client.get_me()
    logger.info(f"Looking up Channel <{config['channel_name']}>...")

    async for dialog in client.iter_dialogs():
        if not dialog.is_channel:
            continue

        channel_name = dialog.name

        if not channel_name.lower().strip() == config['channel_name'].lower().strip():
            continue

        logger.info(
            "Kicking participants who joined during attacks date/time...")
        async for participant in client.iter_participants(dialog):
            participant_info = await client(GetParticipantRequest(dialog, participant))
            if isinstance(participant_info.participant, ChannelParticipantCreator):
                continue
            if within_attack_times(participant_info.participant.date):
                logger.debug(
                    f"Kicking {participant_info.users[0].first_name} {participant_info.users[0].last_name}")
                await client.kick_participant(dialog, participant_info.participant.user_id)
                removed = removed+1

        logger.info("Kicking BOT participants...")
        async for participant in client.iter_participants(dialog, filter=ChannelParticipantsBots()):
            participant_info = await client(GetParticipantRequest(dialog, participant))
            if isinstance(participant_info.participant, ChannelParticipantCreator):
                continue

            logger.debug(
                f"Kicking {participant_info.users[0].first_name} {participant_info.users[0].last_name}")
            await client.kick_participant(dialog, participant_info.participant.user_id)
            removed = removed + 1

        logger.info(
            f"Removed <{removed}> participants from channel <{channel_name}>")

with client:
    client.loop.run_until_complete(main())
