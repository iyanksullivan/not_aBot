import asyncio
import os
from discord import client
from discord.ext.commands.errors import ChannelNotReadable
from dotenv import load_dotenv
from discord.ext import commands,tasks
import discord
import youtube_dl
from random import choice
import urllib.parse, urllib.request, re

#define status
status = ['Watering Plant','Breathing o2','type ?help for help','waiting order from my master']

#setting or config for youtube dl e.g quality etc.
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
#import token
load_dotenv()
TOKEN = os.getenv('DC_Token')
#client and command
bot = commands.Bot(command_prefix='?')

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@tasks.loop(seconds=5)
async def change_stat():
    await bot.change_presence(activity=discord.Game(choice(status)))

@bot.command(name='ping',help='ping the server')
async def ping(ctx):
    await ctx.send(f'iya iya : {round(bot.latency * 1000)}ms')

@bot.command(name='play',help='play music and join voice channel')
async def play(ctx,name):
    query_string = urllib.parse.urlencode({'search_query': name})
    htm_content = urllib.request.urlopen('http://www.youtube.com/results?' + query_string)
    url = re.findall(r'/watch\?v=(.{11})',htm_content.read().decode())
    if not ctx.message.author.voice:
        await ctx.send('Join the voice channel nyan!')
        return
    else:
        channel = ctx.message.author.voice.channel    
    await channel.connect()

    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        player = await YTDLSource.from_url('http://www.youtube.com/watch?v='+url[0],loop=bot.loop,stream=True)
        voice_channel.play(player, after = lambda e:print('Player Error: %s'%e) if e else None)
    await ctx.send(f'Now Playing: {player.title}')

@bot.command(name='stop',help='disconnect me from voice channel')
async def stop(ctx):
    if ctx.message.author.voice:
        voice_client = ctx.message.guild.voice_client
        await voice_client.disconnect()
    else:
        await ctx.send('You are not joining any voice nyan!')

@bot.command(name='whoami',help='Return Im Earth Chan!')
async def whoami(ctx):
    await ctx.send("Hi i'm Earth Chan!")

@bot.command(name='credit',help='Show credit')
async def credit(ctx):
    await ctx.send("gw doang capek anjink pengen jadi bumi")

@bot.event
async def on_ready():
    change_stat.start()
    print("Bot is Active")

bot.run(TOKEN)