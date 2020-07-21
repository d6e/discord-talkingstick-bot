#!/usr/bin/env python3
import os
import discord
from discord.ext import commands
from datetime import datetime, timezone
import json
from os import listdir
from os.path import isfile, isdir, join
import pprint
import urllib.request
import shutil
import time
import typing
from typing import List
import asyncio

pp = pprint.PrettyPrinter(indent=4)

secret_key = os.environ['DISCORD_BOT_SECRET']
vote_emoji = '🎙'
bot = commands.Bot(command_prefix='$')
TALKING_STICK_START_MSG = "Talkingstick mode activated!"

async def get_talkingstick_message(channel):
    async for message in channel.history(limit=100):
        if message.author == bot.user and TALKING_STICK_START_MSG in message.content:
            return message

async def enable_talkingstick(text_channel, voice_channel):
    # save text and voice channels for later
    bot.text_channel = text_channel
    bot.voice_channel = voice_channel
    bot.voice_queue: List[discord.Member] = []
    bot.voice_channel_members = bot.voice_channel.members
    # text_permissions = text_channel.permissions_for(bot.user)
    # voice_permissions = bot.user.permissions_in(voice_channel)
    await text_channel.send(TALKING_STICK_START_MSG +
            "\n- Only the person with the talkingstick may speak."
            "\n- React with {} to be enqueued for the talkingstick.".format(vote_emoji) +
            "\n- Mute yourself when you're ready to give up the talking stick.")
    message = await get_talkingstick_message(text_channel)
    try:
        await message.add_reaction(vote_emoji)
        pins = await message.channel.pins()
        for p in pins:
            if p.author == bot.user:
                await p.unpin()
                await p.delete()
        await message.pin()
        voice_channel = bot.voice_channel
        to_mute = [mute(member) for member in voice_channel.members]
        await asyncio.gather(*to_mute)
    except discord.errors.Forbidden:
        await text_channel.send("ERROR: I lack the 'manage_messages' bot permission.")
        raise

async def disable_talkingstick(text_channel, voice_channel):
    to_unmute = [unmute(member) for member in voice_channel.members]
    await asyncio.gather(*to_unmute)  # unmute all users
    pinned = await get_bots_pinned_message(text_channel)
    if pinned is not None:
        await pinned.unpin()
        await pinned.delete()
    await text_channel.send("talkingstick mode deactivated.")
    bot.text_channel = None
    bot.voice_channel = None
    bot.voice_queue: List[discord.Member] = []
    bot.voice_channel_members = None


@bot.command(usage="$talkingstick [enable <voice_channel> | disable <voice_channel>]")
async def talkingstick(ctx, arg1: str, voice_channel: discord.VoiceChannel, dry_run=None):
    text_channel = ctx.channel
    bot.dry_run = dry_run is not None
    if arg1 == "enable":
        await enable_talkingstick(text_channel, voice_channel)
    elif arg1 == "disable":
        await disable_talkingstick(text_channel, voice_channel)
    else:
        await ctx.send("Invalid argument {}. Usage: {}".format(arg1, ctx.command.usage))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing Required Arguments.\nUsage: "+ctx.command.usage)
    else:
        await ctx.send("{}\nUsage: {}".format(error, ctx.command.usage))
        print(error)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    """ When reaction added, if vote emoji and is talking stick bot emoji """
    if payload.emoji.name != vote_emoji:  # ignore other reactions
        return
    if not hasattr(bot, 'text_channel'): return
    if bot.get_user(payload.user_id).bot: return # ignore bots
    text_channel = bot.text_channel
    member = get_user_from_channel(bot.voice_channel, payload.user_id)
    if member is None:
        await text_channel.send("No one is in the voice channel")
        return
    if payload.emoji.name == vote_emoji:
        bot.voice_queue.append(member)
    response = 'Added {0} to queue {1}'.format(payload.member, [x.name for x in bot.voice_queue])
    await text_channel.send(response)

    if len(bot.voice_queue) == 1:  # if first speaker, then give them the talkingstick
        await text_channel.send("{} has the talkingstick!".format(member))
        await unmute(member)

def get_user_from_channel(channel, user_id):
    for member in channel.members:
        if member.id == user_id:
            return member

async def mute(user):
    print("bot muted {}".format(user.name))
    if not bot.dry_run:
        await user.edit(mute=True)

async def unmute(user):
    print("bot unmuted {}".format(user.name))
    if not bot.dry_run:
        await user.edit(mute=False)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.emoji.name != vote_emoji:  # ignore other reactions
        return
    if not hasattr(bot, 'text_channel'): return
    if bot.get_user(payload.user_id).bot: return # ignore bots
    text_channel = bot.text_channel
    voice_channel = bot.voice_channel
    member = get_user_from_channel(voice_channel, payload.user_id)
    await pass_stick(member)
    response = 'Removed {0} from queue {1}'.format(member, [x.name for x in bot.voice_queue])
    print(response)
    await text_channel.send(response)

async def get_bots_pinned_message(channel):
    pins = await channel.pins()
    for pinned in pins:
        if pinned.author.id == bot.user.id:
            return pinned

async def pass_stick(member: discord.Member):
    if member in bot.voice_queue:
        bot.voice_queue.remove(member)
    if len(bot.voice_queue) > 0:  # pass talking stick to next member
        next_member = bot.voice_queue[0]
        await asyncio.gather(
            mute(member)
            ,unmute(next_member)
            ,bot.text_channel.send("Talkingstick passed to {}".format(next_member))
        )

@bot.event
async def on_voice_state_update(member, before, after):
    if not hasattr(bot, 'text_channel'):
        if member.voice is not None and member.voice.mute:
            print("Bot is not active, unmuting {}".format(member.name))
            await member.edit(mute=False)  # ensure not mute if not active (not very efficient to do this every call, but there's no other way)
        return  # don't continue if bot is not activated
    text_channel = bot.text_channel
    voice_channel = bot.voice_channel
    just_joined = member not in bot.voice_channel_members
    just_left = member.voice is None and member in bot.voice_channel_members
    unmuted_by_self = before.self_mute and not after.self_mute
    muted_by_self = not before.self_mute and after.self_mute
    if just_left:
        print("Member {} left, member count={}".format(member, len(voice_channel.members)))
        bot.voice_channel_members = voice_channel.members
        if len(voice_channel.members) == 0 and bot.voice_channel is not None:  # if voice channel is empty
            await asyncio.gather(
                text_channel.send("The voice channel '{}' is empty now, disabling talkingstick mode.".format(voice_channel))
                ,disable_talkingstick(text_channel, voice_channel)
            )
    if member.voice is None or member.voice.channel != bot.voice_channel:
        return  # don't continue if voice channel isn't the one the bot is paying attention to.
    elif just_joined:
        print("{} user just joined".format(member.name))
        bot.voice_channel_members = voice_channel.members
        await asyncio.gather(
                text_channel.send("Welcome {}, we're in talkingstick mode so you're muted.".format(member)),
                mute(member))
    elif not after.mute and muted_by_self:  # give up speaking stick
        print("{} self muted".format(member.name))
        if member not in bot.voice_queue: return
        await text_channel.send("User {} self-muted and so gave up the speaking stick.".format(member))
        await pass_stick(member)
        pinned = await get_bots_pinned_message(text_channel)
        await pinned.remove_reaction(vote_emoji, member)
    elif unmuted_by_self and after.mute:  # user tries to unmute themselves
        print("{} tried to unmute themselves".format(member.name))
        await text_channel.send("@{} you currently do not have the speaking stick!".format(member))
        try:
            await mute(member)
        except discord.errors.Forbidden:
            await text_channel.send("ERROR: I lack the 'mute_members' bot permission.")
            raise

@bot.event
async def quit(ctx):
    await bot.close()
    # used for closing the bot if you plan to make changes. this can either be entirely removed, or modified so
    # only the bot owner (presumably yourself) can use it. as it stands, any user can use the command and
    # turn off the bot.

bot.run(secret_key)
