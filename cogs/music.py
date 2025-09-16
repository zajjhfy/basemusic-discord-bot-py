import discord
import asyncio
from discord.ext import commands
from discord import app_commands
from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

## MAY BE PROBLEMS WITH JOINING DIFFERENT CHANNELS | 
## VISUAL INTERACTIONS NOT DONE + VISUAL INTERACTIONS WITH COMMANDS NOT DONE
## TODO: QUEUELISTVIEW
class SongListView(discord.ui.View):
    def __init__(self, song_list, music_cog_ref):
        super().__init__(timeout=60)

        self.song_list = song_list
        self.music_cog_ref: MusicCog = music_cog_ref

    @discord.ui.button(label="1", style=discord.ButtonStyle.secondary, row=0)
    async def button1_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    @discord.ui.button(label="2", style=discord.ButtonStyle.secondary, row=0)
    async def button2_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    @discord.ui.button(label="3", style=discord.ButtonStyle.secondary, row=0)
    async def button3_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    @discord.ui.button(label="4", style=discord.ButtonStyle.secondary, row=0)
    async def button4_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    @discord.ui.button(label="5", style=discord.ButtonStyle.secondary, row=0)
    async def button5_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    async def btn_callback(self, interaction, button: discord.ui.Button):
        self.stop()
        await self.music_cog_ref.on_song_chosed(self.song_list[int(button.label)-1], interaction=interaction)

class SongView(discord.ui.View):
    def __init__(self, music_cog_ref):
        super().__init__()

        self.music_cog_ref: MusicCog = music_cog_ref

    @discord.ui.button(emoji="⏯️", style=discord.ButtonStyle.grey, row=0)
    async def button1_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.music_cog_ref.pause_resume_song()

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.grey, row=0)
    async def button2_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog_ref.skip_song(interaction=interaction)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.grey, row=0)
    async def button3_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.music_cog_ref.stop_song(interaction=interaction)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.grey, row=0)
    async def button4_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    @discord.ui.button(emoji="🅿️", style=discord.ButtonStyle.grey, row=0)
    async def button5_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.btn_callback(interaction=interaction, button=button)

    async def btn_callback(self, interaction, button: discord.ui.Button):
        await interaction.response.send_message("В разработке", ephemeral=True)


class MusicCog(commands.Cog):
    def __init__(self, bot: commands.Bot, guild_id):
        self.bot = bot
        self.guild_id = guild_id

        self.songs_queue = []
        self.song_pointer = 0
        self.voice_client: discord.VoiceClient = None

        self.configure_ytdl()
        self.configure_youtube()

    def configure_ytdl(self):
        ytdl_options = {
            'format': 'bestaudio',
            'noplaylist': True
        }
        self.ytdl = YoutubeDL(ytdl_options)
    
    def configure_youtube(self):
        try:
            with open('./api.txt', 'r') as f:
                API_KEY = f.read().strip()
        except:
            print('Api-key not found')

        self.youtube = build('youtube', 'v3', developerKey=API_KEY)
    
    def search_video(self, args : str):
        try:
            request = self.youtube.search().list(
                part="snippet",
                q=args,
                type="video",
                maxResults=5
            )
            response = request.execute()
        except HttpError as e:
            print("HTTP error:", e)
            return []
        except Exception as e:
            print("Error:", e)
            return []

        videos = []
        for item in response.get("items", []):
            video_id = item["id"].get("videoId")
            snippet = item.get("snippet", {})
            videos.append({
                "videoId": video_id,
                "title": snippet.get("title"),
                "channelTitle": snippet.get("channelTitle"),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url")
            })

        return videos

    def get_embed_song_list(self, videos, interaction : discord.Interaction):
        link = "https://www.youtube.com/watch?v="

        embed = discord.Embed(title="Найденные видео", color=discord.Color.blue())
        i = 1
        for video in videos:
            embed.add_field(name=f"{i}. {video["title"]} - {video['channelTitle']}", value=f"[YouTube]({link}{video['videoId']})", inline=False)
            i += 1

        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        return embed

    def get_embed_current_song(self, video, interaction: discord.Interaction):
        link = "https://www.youtube.com/watch?v="

        embed = discord.Embed(title="Сейчас играет", color=discord.Color.green())
        embed.add_field(name=f"{video["title"]} - {video['channelTitle']}", value=f"[YouTube]({link}{video['videoId']})", inline=False)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url=video["thumbnail"])

        return embed
    
    def get_embed_queued_song(self, video, interaction: discord.Interaction):
        link = "https://www.youtube.com/watch?v="

        embed = discord.Embed(title="Добавлено в очередь", color=discord.Color.yellow())
        embed.add_field(name=f"{video["title"]} - {video['channelTitle']}", value=f"[YouTube]({link}{video['videoId']})", inline=False)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed.set_thumbnail(url=video["thumbnail"])

        return embed
    
    def get_response_embed(self, title: str, description: str, color: discord.Color, interaction: discord.Interaction):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)

        return embed

## WORKS : REORGANIZE
    def get_FFMpeg_source(self, song):
        data = self.ytdl.extract_info(song["videoId"], download=False)
        audio_url = data['url']
        
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn' 
        }

        return discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
    
    async def cleanup(self, guild: discord.Guild):
        vc: discord.VoiceClient = guild.voice_client

        if vc and vc.is_playing():
            vc.stop()

        self.songs_queue.clear()
        self.song_pointer = 0

        if vc and vc.is_connected():
            await vc.disconnect(force=True)

    async def on_song_chosed(self, song, interaction: discord.Interaction):
        self.songs_queue.append(song)

        if not self.voice_client or not self.voice_client.is_playing():
            self.song_pointer = len(self.songs_queue) - 1
            await self.play_song(interaction=interaction)
        else:
            embed = self.get_embed_queued_song(video=song, interaction=interaction)
            await interaction.response.edit_message(embed=embed, view=None)

## delete songlist todo
    async def play_song(self, interaction: discord.Interaction):
        if not self.songs_queue or self.song_pointer >= len(self.songs_queue):
            await self.cleanup(interaction.guild)
            return

        song = self.songs_queue[self.song_pointer]
        embed = self.get_embed_current_song(video=song, interaction=interaction)
        song_view = SongView(self)

        if hasattr(self, "player_message"):
            try:
                await self.player_message.delete()
            except:
                pass
        
        self.player_message = await interaction.channel.send(embed=embed, view=song_view)

        source = self.get_FFMpeg_source(song=song)
        self.voice_client = interaction.guild.voice_client

        def after_playing(error):
            if error:
                print(f"Ошибка при проигрывании: {error}")
                
            self.song_pointer += 1

            async def play_next_or_cleanup():
                if self.song_pointer < len(self.songs_queue):
                    await self.play_song(interaction)
                else:
                    self.song_pointer = 0
                    await self.cleanup(interaction.guild)

            self.bot.loop.call_soon_threadsafe(asyncio.create_task, play_next_or_cleanup())

        self.voice_client.play(source, after=after_playing)

    async def stop_song(self, interaction: discord.Interaction):
        await self.cleanup(interaction.guild)

        if not interaction.response.is_done():
            await interaction.response.edit_message(embed = self.get_response_embed(
                                                        title="Остановка воспроизведения",
                                                        description="Бот успешно завершил воспроизведение", 
                                                        color=discord.Color.green(), 
                                                        interaction=interaction
                                                    ), view=None)
        else:
            await interaction.edit_original_response(embed = self.get_response_embed(
                                                        title="Остановка воспроизведения",
                                                        description="Бот успешно завершил воспроизведение", 
                                                        color=discord.Color.green(), 
                                                        interaction=interaction
                                                    ), view=None)

    def pause_resume_song(self):
        if self.is_song_paused():
            self.voice_client.resume()
        else:
            self.voice_client.pause()

    def is_song_paused(self) -> bool:
        if self.voice_client:
            return self.voice_client.is_paused()

    async def skip_song(self, interaction: discord.Interaction):
        if not self.voice_client or not self.voice_client.is_playing():
            await interaction.response.send_message(embed=self.get_response_embed(
                title="Нет песни для пропуска",
                description="Сейчас ничего не воспроизводится",
                color=discord.Color.red(),
                interaction=interaction
            ))

            return

        self.voice_client.stop()

    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.id != self.bot.user.id:
            return

        if before.channel is not None and after.channel is None:
            await self.cleanup(before.channel.guild)

    async def join(self, interaction: discord.Interaction) -> bool:
        if interaction.user.voice is None:
            await interaction.response.send_message(embed = self.get_response_embed(
                                                        title="Вы не в голосовом канале",
                                                        description="Войдите в голосовой канал что начать", 
                                                        color=discord.Color.red(), 
                                                        interaction=interaction))
            return False

        vc: discord.VoiceClient = interaction.guild.voice_client

        if vc is None:
            await interaction.user.voice.channel.connect()
            return True

        if vc.channel is interaction.user.voice.channel:
            return True

        if vc.channel is not interaction.user.voice.channel:
            await vc.disconnect()
            await interaction.user.voice.channel.connect()
            return True

    @app_commands.command(name="leave", description="Выход из голосового канала")
    async def leave(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client

        if vc is not None:
            await self.cleanup(guild=interaction.guild)

            await interaction.response.send_message(embed = self.get_response_embed(
                                                        title="Выход из голосового канала",
                                                        description="Бот успешно завершил воспроизведение", 
                                                        color=discord.Color.green(), 
                                                        interaction=interaction
            ))
            return
        
        await interaction.response.send_message(embed = self.get_response_embed(
                                                        title="Бот не находится в голосовом канале",
                                                        description="Войдите в голосовой канал чтобы использовать эту команду", 
                                                        color=discord.Color.red(), 
                                                        interaction=interaction))
        return
    
    @app_commands.command(name="play", description="Воспроизведение песни")
    async def play(self, interaction: discord.Interaction, song_name : str = ""):
        if song_name == "":
            await interaction.response.send_message(embed = self.get_response_embed(
                                                        title="Нет названия песни",
                                                        description="Введите название песни чтобы начать воспроизведение", 
                                                        color=discord.Color.red(), 
                                                        interaction=interaction))
        else: 
            if await self.join(interaction=interaction):
                videos = self.search_video(song_name)
                embed = self.get_embed_song_list(videos=videos, interaction=interaction)

                view = SongListView(song_list=videos, music_cog_ref=self)
                await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="stop", description="Остановка воспроизведения")
    async def stop(self, interaction: discord.Interaction):
        await self.stop_song(interaction=interaction)

    @app_commands.command(name="skip", description="Пропуск песни")
    async def skip(self, interaction: discord.Interaction):
        await self.skip_song(interaction=interaction)
    
    @app_commands.command(name="pause", description="Возобновить/остановить воспроизведение")
    async def pause(self, interaction: discord.Interaction):
        self.pause_resume_song()

    @app_commands.command(name="queue", description="Показать очередь песен")
    async def queue(self, interaction: discord.Interaction):
        await interaction.response.send_message("В разработке", ephemeral=True)

    def cog_load(self):
        self.bot.tree.add_command(self.leave, guild=self.guild_id)
        self.bot.tree.add_command(self.play, guild=self.guild_id)
        self.bot.tree.add_command(self.stop, guild=self.guild_id)
        self.bot.tree.add_command(self.pause, guild=self.guild_id)
        self.bot.tree.add_command(self.skip, guild=self.guild_id)