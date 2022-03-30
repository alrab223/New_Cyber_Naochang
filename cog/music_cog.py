import asyncio
import glob
import os
import random

import discord
from discord.ext import commands
from gtts import gTTS
from cog.util.DbModule import DbModule as db


# コグとして用いるクラスを定義。
class Music(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.volume = 0.1
      self.voich = None
      self.read = False
      self.flag = False
      self.db = db()

   @commands.slash_command(name="botをボイスチャンネルに召喚", guild_ids=[os.getenv("FotM")])
   async def voice_connect(self, ctx):
      """botをボイチャに召喚します"""
      self.voich = await discord.VoiceChannel.connect(ctx.author.voice.channel)
      self.voich.play(discord.FFmpegPCMAudio('music/nao_aisatsu.m4a'))
      self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
      self.voich.source.volume = self.volume
      await asyncio.sleep(2)

   @commands.slash_command(name="botをボイスチャンネルから退出", guild_ids=[os.getenv("FotM")])
   async def voice_disconnect(self, ctx):
      """botをボイチャから退出させます"""
      if self.voich.is_playing():
         self.voich.stop()
      self.voich.play(discord.FFmpegPCMAudio("music/se/hayate_tanosikatta.m4a"))
      await asyncio.sleep(2)
      await self.voich.disconnect()
      self.voich = None

   @commands.slash_command(name="音楽を流す", guild_ids=[os.getenv("FotM")])
   async def BGM_select(self, ctx, genre: str = "instrumental"):
      """BGMを流します"""
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

   @commands.slash_command(name="音楽をスキップ", guild_ids=[os.getenv("FotM")])
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

   @commands.slash_command(name="音楽を一時停止", guild_ids=[os.getenv("FotM")])
   async def pause(self, ctx):
      """ポーズ"""
      if self.voich.is_playing():
         self.voich.pause()

   @commands.slash_command(name="音楽を停止", guild_ids=[os.getenv("FotM")])
   async def stop(self, ctx):
      """停止"""
      self.db.update("delete from music")
      if self.voich.is_playing():
         self.voich.stop()

   @commands.slash_command(name="音楽を再開", guild_ids=[os.getenv("FotM")])
   async def restart(self, ctx):
      """再開"""
      if self.voich.is_playing():
         pass
      else:
         self.voich.resume()

   @commands.slash_command(name="ボリューム調整", guild_ids=[os.getenv("FotM")])
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

   @commands.command("調教")
   async def se_training(self, ctx, train):
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
      await ctx.send(f"調教しました({train[0]}={train[1]})")

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

   @commands.command("読み上げ")
   async def reads(self, ctx):
      if self.read:
         self.read = False
         await ctx.send("読み上げをオフにしました")
      else:
         self.read = True
         await ctx.send("読み上げをオンにしました")
         await self.Voice_Read()

   @commands.Cog.listener()
   async def on_message(self, message):
      if message.content.startswith("<") is False and message.content.startswith("!") is False and message.content.startswith(
         "http") is False and self.read and message.author.bot is False and message.channel.id == os.getenv("Voice_Channel"):
         text = message.content
         self.db.allinsert("read_text", [message.author.id, message.id, text])

   # @commands.Cog.listener()
   # async def on_voice_state_update(self, member, before, after):
   #    if member.bot:
   #       return

   #    # ボイチャ通知処理

   #    if before.channel is None and self.voich is not None:
   #       row = self.db.select(f"select * from enter_se where id={member.id}")
   #       if row[0]["se"] != "":
   #          self.voich.play(discord.FFmpegPCMAudio(row[0]["se"]))
   #       if row[0]["volume"] is not None:
   #          self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
   #          self.voich.source.volume = row[0]["volume"]


def setup(bot):

   bot.add_cog(Music(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。
