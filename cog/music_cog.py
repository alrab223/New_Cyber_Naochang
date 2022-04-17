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
      self.read_channel = None

   @commands.slash_command(name="botをボイスチャンネルに召喚", guild_ids=[os.getenv("FotM"), os.getenv("Jikken_Guild")])
   async def voice_connect(self, ctx):
      """botをボイチャに召喚します"""
      self.voich = await discord.VoiceChannel.connect(ctx.author.voice.channel)

   @commands.slash_command(name="botをボイスチャンネルから退出", guild_ids=[os.getenv("FotM"), os.getenv("Jikken_Guild")])
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

   @commands.slash_command(name="調教", guild_ids=[os.getenv("FotM"), os.getenv("Jikken_Guild")])
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

   @commands.slash_command(name="読み上げ", guild_ids=[os.getenv("FotM"), os.getenv("Jikken_Guild")])
   async def reads(self, ctx):
      """このコマンドを使用したチャンネルの書き込みを読み上げます"""
      if self.read:
         self.read = False
         await ctx.respond("読み上げをオフにしました")
      else:
         self.read = True
         await ctx.respond("読み上げをオンにしました")
         self.read_channel = ctx.channel.id
         await self.Voice_Read()

   @commands.Cog.listener()
   async def on_message(self, message):
      if message.content.startswith("<") is False and message.content.startswith("!") is False and message.content.startswith(
         "http") is False and self.read and message.author.bot is False and message.channel.id == self.read_channel:
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
