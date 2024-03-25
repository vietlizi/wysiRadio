import discord
import youtube_dl
from discord.ext import commands

TOKEN = 'YOUR_DISCORD_BOT_TOKEN'
PREFIX = '!'

intents = discord.Intents.default()
intents.voice_states = True
intents.members = True
intents.presences = True  # Enable presence intent
intents.guilds = True  # Enable guilds intent

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

def check_queue(ctx, queue):
    if len(queue) == 0:
        return
    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        return
    if vc.is_playing():
        return
    song = queue[0]
    play_song(ctx, song, queue)

def play_song(ctx, song, queue):
    vc = ctx.voice_client

    def play_error(e):
        if vc.is_connected():
            ctx.bot.loop.create_task(vc.disconnect())
        queue.clear()
        ctx.bot.loop.create_task(ctx.send(f'Error: {str(e)}'))

    try:
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song['url'], **ytdl_format_options))
        vc.play(source, after=lambda _: check_queue(ctx, queue))
        vc.source = discord.PCMVolumeTransformer(vc.source)
        vc.source.volume = 0.5
    except Exception as e:
        play_error(e)

@bot.command(name='play', help='Plays a song from YouTube URL')
async def play(ctx, url):
    voice_channel = ctx.author.voice.channel
    if voice_channel is None:
        await ctx.send('You must be in a voice channel to use this command!')
        return

    try:
        channel = voice_channel.connect()
    except:
        channel = ctx.voice_client

    if not channel:
        await ctx.send('Bot is not in a voice channel.')
        return

    with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']

    song = {'title': info['title'], 'url': url2}

    if 'queue' not in ctx.bot.__dict__:
        ctx.bot.__dict__['queue'] = []

    ctx.bot.__dict__['queue'].append(song)

    if not channel.is_playing():
        play_song(ctx, song, ctx.bot.__dict__['queue'])
    else:
        await ctx.send(f'Added to queue: {song["title"]}')

@bot.command(name='skip', help='Skips the current song')
async def skip(ctx):
    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        await ctx.send('I am not currently connected to a voice channel.')
        return
    if vc.is_playing():
        vc.stop()
        await ctx.send('Skipped the song!')
    else:
        await ctx.send('There is no song to skip!')

@bot.command(name='stop', help='Stops the music and clears the queue')
async def stop(ctx):
    vc = ctx.voice_client
    if not vc or not vc.is_connected():
        await ctx.send('I am not currently connected to a voice channel.')
        return
    if vc.is_playing():
        vc.stop()
    ctx.bot.__dict__['queue'] = []
    await vc.disconnect()
    await ctx.send('Music stopped and queue cleared!')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

bot.run(TOKEN)
