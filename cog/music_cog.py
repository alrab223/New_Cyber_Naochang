import asyncio
import glob
import os
import re
import random
import datetime

import discord
from discord.ext import commands
from gtts import gTTS

from cog.util.DbModule import DbModule as db

class Music(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.volume = 0.1
      self.voich = None
      self.flag = False
      self.db = db()
      self.read_channel = None
      self.read = self.db.select("select * from flag_control where flag_name='read_text'")[0]["flag"]

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
      if self.read == 1:
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

   # 読み上げるデータの前処理
   def se_preprocessing(self, text, sounds):
      create_text = ""  # SEを混ぜるための一時変数
      voice_data = {}  # テキストとSEの情報を入れる変数
      counter = 1  # 分割数の管理
      for i in list(text):
         create_text += i
         for se_data in sounds:
            if se_data["word"] == create_text and se_data["short"] == 1:
               voice_data[str(counter)] = {"type": "se", "volume": se_data["volume"], "path": se_data["sound_path"]}
               create_text = ""
               counter += 1
            elif se_data["word"] in create_text and se_data["short"] == 1:
               word = create_text.replace(se_data["word"], "")
               voice_data[str(counter)] = {"type": "text", "word": word}
               counter += 1
               voice_data[str(counter)] = {"type": "se", "volume": se_data["volume"], "path": se_data["sound_path"]}
               create_text = ""
               counter += 1
      if voice_data == {}:  # SEが無かった場合
         voice_data[str(counter)] = {"type": "text", "word": text}
      return voice_data

   # 読み上げ処理
   async def Voice_Read(self, text):
      while self.voich.is_playing() is True:
         await asyncio.sleep(0.5)
      sounds = self.db.select("select *from read_text_se order by priority asc")  # SE一覧
      voice_data = self.se_preprocessing(text, sounds)  # 読み上げテキストの前処理
      print(voice_data)
      for voice in voice_data.values():
         if voice["type"] == "se":
            self.voich.play(discord.FFmpegPCMAudio(voice["path"]))
            self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
            self.voich.source.volume = voice["volume"]
         else:
            try:
               text = self.read_convert(voice["word"])
               tts = gTTS(text=text, lang='ja')
               path = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
               tts.save(f'music/mp3/{path}.mp3')
               self.voich.play(discord.FFmpegPCMAudio(f'music/mp3/{path}.mp3'))
               self.voich.source = discord.PCMVolumeTransformer(self.voich.source)
               self.voich.source.volume = 0.5
            except AssertionError:
               await asyncio.sleep(0.5)
         while self.voich.is_playing() is True:  # 再生が終わるまで待機
            await asyncio.sleep(0.5)

   @commands.slash_command(name="読み上げ")
   async def reads(self, ctx):
      if self.read == 1:
         self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "read_text"})
         self.read = 0
         await ctx.respond("読み上げをオフにしました")
         self.db.auto_delete("channel_flag_control", {"flag_name": "read_text"})
         files = glob.glob("music/mp3/*.mp3")
         for f in files:
            os.remove(f)
      else:
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "read_text"})
         self.read = 1
         await ctx.respond("読み上げをオンにしました")
         self.db.allinsert("channel_flag_control", [None, ctx.channel.id, "read_text"])
         self.db.update("delete from read_text")

   @commands.slash_command(name="読み上げうるせえ")
   async def read_stop(self, ctx):
      '''今読み上げているテキストを停止'''
      if self.voich.is_playing():
         self.voich.stop()

   @commands.slash_command(name="ボイチャ来場者通知モード")
   async def announce_vc(self, ctx, vc_id=None, announce_channel_id=None):
      """ボイチャに入ってきた人を通知"""
      flag = self.db.select("select * from flag_control where flag_name='announce_vc'")
      if flag[0]["flag"] == 0:
         if vc_id is None:
            await ctx.respond("VCのIDを引数に入れてください")
            return
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "announce_vc"})
         self.db.allinsert("channel_flag_control", [int(vc_id), announce_channel_id, "announce_vc"])
         await ctx.respond("VC来場者管理モードをオンにしました")
      else:
         await ctx.respond("VC来場者管理モードをオフにしました")
         self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "announce_vc"})
         self.db.auto_delete("channel_flag_control", {"flag_name": "announce_vc"})

   # 読み上げるテキストの加工
   def read_censorship(self, text):
      pattern = "https?://[\\w/:%#\\$&\\?\\(\\)~\\.=\\+\\-]+"
      text = re.sub(pattern, "URL省略", text)
      if text.startswith("<"):
         return False
      elif text.startswith("!"):
         return False
      elif text.count(os.linesep) > 4:
         text = "改行が多数検出されたため、省略します"
      elif len(text) > 100:
         text = "文字数が多いか、怪文書が検出されましたので省略します"
      return text

   # メッセージが書き込まれた時の処理
   @commands.Cog.listener()
   async def on_message(self, message):
      if self.read == 1 and message.author.bot is False and self.voich is not None:
         channel_id = self.db.select("select *from channel_flag_control where flag_name='read_text'")[0]["channel_id"]
         if message.channel.id == channel_id:
            text = self.read_censorship(message.content)  # 一部文字列の処理
            if text is not False:
               await self.Voice_Read(text)

   @commands.Cog.listener()
   async def on_voice_state_update(self, member, before, after):
      flag = self.db.select("select * from flag_control where flag_name='announce_vc'")[0]["flag"]
      if member.bot or flag == 0:
         return
      channel_id = self.db.select("select * from channel_flag_control where flag_name='announce_vc'")[0]
      channel = self.bot.get_channel(channel_id["channel_id"])
      if before.channel is None and after.channel.id == channel_id["vc_channel_id"]:
         msg = await channel.send(f"{member.display_name}さんが来たよ！みんな手を振って！")
         await asyncio.sleep(10)
         await msg.delete()

      elif after.channel is None and before.channel.id == channel_id["vc_channel_id"]:
         msg = await channel.send(f"{member.display_name}さんまたね～")
         await asyncio.sleep(10)
         await msg.delete()


def setup(bot):

   bot.add_cog(Music(bot))
