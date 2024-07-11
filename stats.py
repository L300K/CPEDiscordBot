import discord
import json
from discord import app_commands
from discord.ext import commands, tasks
import pytz
import re
from datetime import datetime

activity = discord.Activity(type=discord.ActivityType.playing, name="| STATS |")
bot = commands.Bot(command_prefix = "!", activity=activity, status=discord.Status.online, intents = discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    update_member_count.start()
    update_thailand_time.start()
    update_member_status.start()

@tasks.loop(seconds=30)
async def update_member_count():
    guild = bot.get_guild(1115979686820982854)
    if guild:
        voice_channel = guild.get_channel(1132410733255209012)
        if voice_channel:
            member_count = len(guild.members)
            new_channel_name = f'Members: {member_count}'
            if voice_channel.name != new_channel_name:
                await voice_channel.edit(name=new_channel_name)
                print(f'Updated member count in {voice_channel.name}')

@tasks.loop(seconds=30)
async def update_member_status():
    guild = bot.get_guild(1115979686820982854)
    if guild:
        voice_channel = guild.get_channel(1132410910766538916)
        if voice_channel:
            online_count = sum(1 for member in guild.members if member.status == discord.Status.online)
            offline_count = sum(1 for member in guild.members if member.status == discord.Status.offline)
            idle_count = sum(1 for member in guild.members if member.status == discord.Status.idle)
            do_not_disturb_count = sum(1 for member in guild.members if member.status == discord.Status.do_not_disturb)
            new_channel_name = f"🟢 {online_count} 🔴 {offline_count} ⛔️ {do_not_disturb_count} 🌙 {idle_count}"
            new_numbers = ''.join(re.findall(r'\d+', str(new_channel_name)))
            old_numbers = ''.join(re.findall(r'\d+', str(voice_channel.name)))
            if old_numbers != new_numbers:
                await voice_channel.edit(name=new_channel_name)
                print(f'Updated member status in {voice_channel.name}')

@tasks.loop(seconds=60)
async def update_thailand_time():
    guild = bot.get_guild(1115979686820982854)
    if guild:
        voice_channel = guild.get_channel(1132410938667053116)
        if voice_channel:
            thailand_tz = pytz.timezone('Asia/Bangkok')
            thailand_time = datetime.now(thailand_tz)
            formatted_time = thailand_time.strftime('%A, %d %B')
            new_channel_name = f'{formatted_time}'
            if voice_channel.name != new_channel_name:
                await voice_channel.edit(name=new_channel_name)
                print(f'Updated Thailand time in {voice_channel.name}')

@bot.event
async def on_member_join(member):
    update_member_count()
    update_member_status()
    update_thailand_time()
@bot.event
async def on_member_remove(member):
    update_member_count()
    update_member_status()
    update_thailand_time()

bot.run('MTEzMjYxNjg5NzMyNjc1MTc1NA.GOXBWA.JyXMR98PLZEyL26r1WViLZXsGoebzwIPNky2N8')