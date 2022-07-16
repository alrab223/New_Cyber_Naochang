import asyncio
import glob
import os
import re
import random

import discord
from discord.ext import commands
from gtts import gTTS

from cog.util.DbModule import DbModule as db
from cog.util.youtube import YTDLSource


class Music(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.volume = 0.1
      self.voich = None
      self.read = False
      self.flag = False
      self.db = db()
      self.read_channel = None

   @commands.slash_command(name="botをボイスチャンネルに召喚")
   async def voice_connect(self, ctx):
      """botをボイチャに召喚します"""
      self.voich = await discord.VoiceChannel.connect(ctx.author.voice.channel)

   @commands.slash_command(name="botをボイスチャンネルから退出")
   async def voice_disconnect(self, ctx):
      """botをボイチャから退出させます"""
      if self.voich.is_playing():
         self.voich.stop()
      await self.voich.disconnect()
      self.voich = None

   @commands.slash_command(name="音楽を流す")
   async def BGM_select(self, ctx, genre: str = "instrumental"):
      """BGMを流します。読み上げ機能が有効の時は使えません"""
      if self.read is True:
         await ctx.respond("読み上げ機能が有効なため、現在使えません")
         return
      if self.voich.is_playing():
         self.voich.stop()
      files = []
      for i in [f"music/{genre}/*.m4a", f"music/{genre}/*.mp3"]:
         files.append(glob.glob(i))
      files = files[0] + files[1]
      random.shuffle(files)
      self.db.update("delete from music")
      await ctx.send("再生します。お待ちください")
      for file in files:
         self.db.allinsert("music", [file])
      music = self.db.select("select *from music limit 1")[0]['name']
      self.db.auto_delete("music", {"name": music})
      if os.path.exists(music) and "mp3" in music:
         self.voich.play(discord.FFmpegPCMAudio(music), after=self.next)
      else:
         self.voich.play(discord.FFmpegPCMAudio(music), after=self.next)
      self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
      self.voich.source.volume = self.volume

   def next(self, er):
      try:
         music = self.db.select("select *from music limit 1")[0]['name']
         self.db.auto_delete("music", {"name": music})
         if os.path.exists(music) and "mp3" in music:
            self.voich.play(discord.FFmpegPCMAudio(music), after=self.next)
         else:
            self.voich.play(discord.FFmpegPCMAudio(music), after=self.next)
         self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
         self.voich.source.volume = self.volume
      except IndexError:
         return

   @commands.slash_command(name="skip")
   async def skip(self, ctx):
      if self.voich.is_playing():
         self.voich.stop()
      music = self.db.select("select *from music limit 1")[0]["music"]
      self.db.auto_delete("music", {"name": music})
      if os.path.exists(music) and "mp3" in music:
         self.voich.play(discord.FFmpegPCMAudio(music), after=self.next)
      else:
         self.voich.play(discord.FFmpegPCMAudio(music), after=self.next)
      self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
      self.voich.source.volume = self.volume

   @commands.slash_command(name="pause")
   async def pause(self, ctx):
      """音楽を一時停止"""
      if self.voich.is_playing():
         self.voich.pause()

   @commands.slash_command(name="stop")
   async def stop(self, ctx):
      """音楽を停止"""
      self.db.update("delete from music")
      if self.voich.is_playing():
         self.voich.stop()

   @commands.slash_command(name="restart")
   async def restart(self, ctx):
      """音楽を再開"""
      if self.voich.is_playing():
         pass
      else:
         self.voich.resume()

   @commands.slash_command(name="volume")
   async def volume(self, ctx, num: int):
      """ボリュームを調整します(0～100)"""
      self.volume = num * 0.01
      self.voich.source.volume = self.volume
      await ctx.send(f"ボリュームを{num}%に変更しました")

   def read_convert(self, text):
      words = self.db.select("select *from read_se_convert")
      for word in words:
         if word["word"] in text:
            text = text.replace(word["word"], word["yomi"])
      print(text)
      return text

   @commands.slash_command(name="調教")
   async def se_training(self, ctx, train):
      """読み上げの調教をします(単語=読み)"""
      train = train.split("=")
      words = self.db.select("select *from read_se_convert")
      for word in words:
         if word["word"] == train[0]:
            await ctx.send(f"すでに同じ単語が登録されています。上書きしますか？(元の読み方 : {word['word']}={word['yomi']})")

            def user_check(message):
               return message.author.id == ctx.author.id
            msg = await self.bot.wait_for('message', check=user_check)
            if msg.content == "はい":
               self.db.update(f"update read_se_convert set yomi='{train[1]}' where word='{train[0]}'")
               await ctx.send(f"調教しました({train[0]}={train[1]})")
            return

      self.db.allinsert("read_se_convert", [train[0], train[1]])
      await ctx.respond(f"調教しました({train[0]}={train[1]})")

   async def Voice_Read(self):
      while self.read is True:
         if self.voich.is_playing():
            await asyncio.sleep(0.5)
            continue
         se_flag = False
         text = self.db.select("select *from read_text limit 1")
         if text != []:
            self.db.update(f"delete from read_text where text_id={text[0]['text_id']}")
            sounds = self.db.select("select *from read_text_se")
            for se in sounds:
               if text[0]['text'] == se["word"]:
                  self.voich.play(discord.FFmpegPCMAudio(se["sound_path"]))
                  self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
                  self.voich.source.volume = se["volume"]
                  se_flag = True
                  break
            if se_flag is False:
               try:
                  text = self.read_convert(text[0]["text"])
                  tts = gTTS(text=text, lang='ja')
                  tts.save('music/mp3/voice.mp3')
                  self.voich.play(discord.FFmpegPCMAudio('music/mp3/voice.mp3'))
                  self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
                  self.voich.source.volume = 0.5
               except AssertionError:
                  await asyncio.sleep(0.5)
         else:
            await asyncio.sleep(0.5)

   @commands.slash_command(name="読み上げ")
   async def reads(self, ctx):
      """このコマンドを使用したチャンネルの書き込みを読み上げます"""
      if self.read:
         self.read = False
         await ctx.respond("読み上げをオフにしました")
      else:
         self.read = True
         await ctx.respond("読み上げをオンにしました")
         self.read_channel = ctx.channel.id
         self.db.update("delete from read_text")
         await self.Voice_Read()

   @commands.slash_command(name="ボイチャ来場者通知モード")
   async def announce_vc(self, ctx, vc_id=None):
      """ボイチャに入ってきた人を通知"""
      flag = self.db.select("select * from flag_control where flag_name='announce_vc'")
      if flag[0]["flag"] == 0:
         if vc_id is None:
            await ctx.respond("VCのIDを引数に入れてください")
            return
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "announce_vc"})
         self.db.allinsert("channel_flag_control", [int(vc_id), ctx.channel.id, "announce_vc"])
         await ctx.respond("VC来場者管理モードをオンにしました")
      else:
         await ctx.respond("VC来場者管理モードをオフにしました")
         self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "announce_vc"})
         self.db.auto_delete("channel_flag_control", {"flag_name": "announce_vc"})

   def read_censorship(self, text):
      pattern = "https?://[\\w/:%#\\$&\\?\\(\\)~\\.=\\+\\-]+"
      text = re.sub(pattern, "URL省略", text)
      if text.startswith("<"):
         return False
      elif text.startswith("!"):
         return False
      elif len(text) > 100:
         text = "文字数が多いか、怪文書が検出されましたので省略します"
      return text

   async def youtube_next(self):
      while True:
         if self.voich.is_playing():
            await asyncio.sleep(5)
         else:
            if self.pause is True:
               continue
            try:
               music = self.db.select("select *from music limit 1")[0]['name']
               channel = self.bot.get_channel(590521717408137232)
               thread = channel.guild.get_thread(955505294845288511)
               self.db.auto_delete("music", {"name": music})
               player = await YTDLSource.from_url(music, loop=self.bot.loop)
               self.voich.play(player)
               self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
               self.voich.source.volume = self.volume
               embed = discord.Embed(title="再生中の曲", description=f"再生中：{player.title}")
               await thread.send(embed=embed)
            except IndexError:
               files = glob.glob("*.webm")
               for file in files:
                  os.remove(file)
               return

   @commands.slash_command(name="youtubeを流す")
   async def youtube_play(self, ctx, url: str):
      if self.voich.is_playing():
         self.db.allinsert("music", [url])
         await ctx.respond("キューに登録しました")
         return
      player = await YTDLSource.from_url(url, loop=self.bot.loop)
      self.voich.play(player)
      self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
      self.voich.source.volume = self.volume
      await ctx.send(f"再生中：{player.title}")
      await self.youtube_next()

   @commands.Cog.listener()
   async def on_message(self, message):
      if self.read and message.author.bot is False and message.channel.id == self.read_channel:
         text = self.read_censorship(message.content)  # URLの場合、読み上げない
         if text is not False:
            self.db.allinsert("read_text", [message.author.id, message.id, text])

   @commands.Cog.listener()
   async def on_voice_state_update(self, member, before, after):
      flag = self.db.select("select * from flag_control where flag_name='announce_vc'")[0]["flag"]
      if member.bot or flag == 0:
         return
      channel_id = self.db.select("select * from channel_flag_control where flag_name='announce_vc'")[0]
      channel = self.bot.get_channel(channel_id["announce_channel_id"])
      if before.channel is None and after.channel.id == channel_id["vc_id"]:
         msg = await channel.send(f"{member.display_name}さんが来たよ！みんな手を振って！")
         await asyncio.sleep(10)
         await msg.delete()

      elif after.channel is None and before.channel.id == channel_id["vc_id"]:
         msg = await channel.send(f"{member.display_name}さんまたね～")
         await asyncio.sleep(10)
         await msg.delete()


def setup(bot):

   bot.add_cog(Music(bot))
