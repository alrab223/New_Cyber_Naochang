import json
import os
import subprocess
import glob
import traceback

import cv2
import discord
import requests
from discord.ext import commands
from yolov5 import detect

from cog.util import colla
from cog.util import file_download as pd
from cog.util.DbModule import DbModule as db


class Main(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.db = db()
      with open("json/picture.json", "r") as f:
         self.colla_num = json.load(f)

   @commands.is_owner()
   @commands.command("goodbye")
   async def disconnect(self, ctx):
      """botを切ります"""
      await ctx.send("また会いましょう")
      await self.bot.logout()

   @commands.command()
   async def ping(self, ctx):
      await ctx.send(f'応答速度:{round(self.bot.latency * 1000)}ms')

   @commands.is_owner()
   @commands.slash_command(name="reload", guild_ids=[os.getenv("FotM")])
   async def reload(self, ctx):
      """コグをリロードします"""
      cog_path = glob.glob("cog/*.py")
      cog_path = [x.replace("/", ".") for x in cog_path]
      cog_path = [x.replace(".py", "") for x in cog_path]
      await ctx.respond("リロードしました", ephemeral=True)
      INITIAL_EXTENSIONS = cog_path
      for cog in INITIAL_EXTENSIONS:
         try:
            self.bot.reload_extension(cog)
         except Exception:
            traceback.print_exc()

   @commands.Cog.listener()
   async def on_member_join(self, member):
      dm_channel = await member.create_dm()
      with open("text/introduce.txt", "r")as f:
         text = f.read()
      await dm_channel.send(member.mention)
      await dm_channel.send(text)
      self.db.allinsert("user_data", [member.id, 10000, None, 0, 0, 10])

   @commands.command()
   async def server_status(self, ctx):
      text = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE, text=True).stdout.strip().split("=")
      text2 = subprocess.run(['free', '-m'], stdout=subprocess.PIPE, text=True).stdout.strip().split("=")
      text2 = text2[0].split(':')[1].split(' ')
      text2 = [x for x in text2 if x != '']
      embed = discord.Embed(title="サーバー状態")
      embed.add_field(name="CPU温度", value=f"{text[1]}")
      embed.add_field(name="メモリ使用量", value=f"{text2[1]}/{text2[0]}M")
      await ctx.send(embed=embed)

   @commands.Cog.listener()
   async def on_message(self, message):
      if message.author.bot:
         return
      if message.attachments:
         if message.content in self.colla_num:
            pd.download_img(
                message.attachments[0].url,
                "picture/colla/image.png")
            colla.colla_maker(self.colla_num[message.content])
            await message.delete()
            await message.channel.send(file=discord.File("picture/colla/new.png"))

         elif message.content == "切り抜き":
            pd.download_img(
                message.attachments[0].url,
                "picture/colla/image.png")
            response = requests.post(
                'https://api.remove.bg/v1.0/removebg',
                files={'image_file': open('picture/colla/image.png', 'rb')},
                data={'size': 'auto'},
                headers={'X-Api-Key': os.environ.get("removebg_api")},
            )
            if response.status_code == requests.codes.ok:
               with open('picture/colla/no-bg.png', 'wb') as out:
                  out.write(response.content)
            else:
               print("Error:", response.status_code, response.text)
            await message.delete()
            await message.channel.send(file=discord.File("picture/colla/no-bg.png"))

         elif message.content == "アイドル検索":
            pd.download_img(message.attachments[0].url, "yolov5/data/images/image.png")
            idols, img = detect.main("yolov5/data/images/image.png")
            if idols == []:
               await message.reply("誰も検出されませんでした")
               return
            idols = list(set(idols))
            with open("json/idol_classes.json")as f:
               dic = json.load(f)
            s = ""
            for i in idols:
               name = dic[i]
               s += name + "\n"
            s += "を検出しました"
            await message.reply(s)
            cv2.imwrite("yolov5/data/result/image.png", img)


def setup(bot):
   bot.add_cog(Main(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。
