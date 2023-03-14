import os
import subprocess
import glob
import traceback
import json
import datetime

import discord
from discord.ext import commands
import yolov5
import gspread

from cog.util import image_processing
from cog.util import file_download as pd
from cog.util.DbModule import DbModule as db


class Main(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.db = db()
      self.model = yolov5.load('model/Cinderella.pt')  # モデルの読み込み
      self.model.conf = 0.45

   @commands.is_owner()
   @commands.command("goodbye")
   async def disconnect(self, ctx):  # botを切断する
      """botを切ります"""
      await ctx.send("また会いましょう")
      await self.bot.logout()

   @commands.command()
   async def spread(self, ctx):
      gc = gspread.service_account(filename="json/key.json")
      sh = gc.open("記念日一覧").sheet1
      data_list = sh.get_all_values()
      now = datetime.datetime.now()
      day = f"{now.month}/{now.day}"
      for i in data_list[1::]:
         if i[0] == day:
            text = f"今日は{i[1]}です。\n{i[2]}"
            await ctx.send(text)
            if i[3] != "":
               await ctx.send(i[3])

   @commands.command()  # bot動作テスト
   async def ping(self, ctx):
      await ctx.send(f'応答速度:{round(self.bot.latency * 1000)}ms')

   @commands.Cog.listener()  # 新規サーバー参加者の処理
   async def on_member_join(self, member):
      self.db.allinsert("user_data", [member.id, 10000, None, 0, 0, 10])

   @commands.command()
   async def server_status(self, ctx):  # サーバーの状態を調べる
      text = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE, text=True).stdout.strip().split("=")
      text2 = subprocess.run(['free', '-m'], stdout=subprocess.PIPE, text=True).stdout.strip().split("=")
      text2 = text2[0].split(':')[1].split(' ')
      text2 = [x for x in text2 if x != '']
      embed = discord.Embed(title="サーバー状態")
      embed.add_field(name="CPU温度", value=f"{text[1]}")
      embed.add_field(name="メモリ使用量", value=f"{text2[1]}/{text2[0]}M")
      await ctx.send(embed=embed)

   @commands.is_owner()
   @commands.slash_command(name="reload", guild_ids=[os.getenv("FotM")])
   async def reload(self, ctx):
      """コグをリロードします"""
      cog_path = glob.glob("cog/*.py")
      cog_path = [x.replace("/", ".") for x in cog_path]
      cog_path = [x.replace(".py", "") for x in cog_path]
      cog_path = [x for x in cog_path if x != "cog.timeprocess_cog"]
      await ctx.respond("リロードしました", ephemeral=True)
      INITIAL_EXTENSIONS = cog_path
      for cog in INITIAL_EXTENSIONS:
         try:
            self.bot.reload_extension(cog)
            await self.bot.sync_commands()
         except Exception:
            traceback.print_exc()

   @commands.Cog.listener()
   async def on_message(self, message):
      if message.author.bot:
         return
      if message.attachments and message.content != "":
         pd.download_img(message.attachments[0].url, "picture/image_processing/image.png")  # 画像を保存
         process = image_processing.image_processing(message.content)  # 画像処理に関する関数
         if process is True:  # 処理が行われていれば送信
            await message.delete()
            await message.channel.send(file=discord.File("picture/image_processing/new.png"))

         elif message.content == "投票ツイート":
            img = "picture/image_processing/yolo.png"
            pd.download_img(message.attachments[0].url, img)
            results = self.model(img).pred[0]
            predictions = results
            with open("json/idol_classes.json", "r")as f:
               dic = json.load(f)
            name = [x for x in dic.values()]
            idols = []
            for i in predictions[:, 5]:  # 検出したキャラを割り出す
               idols.append(name[int(i.item())])
            text = "「Stage for Cinderella」予選グループBでこの5人に投票しました!!\n#StageforCinderella #SfC予選B #デレステ\n"
            for i in idols:
               text += f"#{i} "
            await message.channel.send(text)


def setup(bot):
   bot.add_cog(Main(bot))
