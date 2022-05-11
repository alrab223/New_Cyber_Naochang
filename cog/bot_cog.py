import os
import subprocess
import glob
import traceback

import discord
from discord.ext import commands
# from yolov5 import detect

from cog.util import image_processing
from cog.util import file_download as pd
from cog.util.DbModule import DbModule as db


class Main(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.db = db()

   @commands.is_owner()
   @commands.command("goodbye")
   async def disconnect(self, ctx):  # botを切断する
      """botを切ります"""
      await ctx.send("また会いましょう")
      await self.bot.logout()

   @commands.command()  # bot動作テスト
   async def ping(self, ctx):
      await ctx.send(f'応答速度:{round(self.bot.latency * 1000)}ms')

   @commands.Cog.listener()
   async def on_member_join(self, member):
      dm_channel = await member.create_dm()
      with open("text/introduce.txt", "r")as f:
         text = f.read()
      await dm_channel.send(member.mention)
      await dm_channel.send(text)
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

         # elif message.content == "アイドル検索":
         #    pd.download_img(message.attachments[0].url, "yolov5/data/images/image.png")
         #    idols, img = detect.main("yolov5/data/images/image.png")
         #    if idols == []:
         #       await message.reply("誰も検出されませんでした")
         #       return
         #    idols = list(set(idols))
         #    with open("json/idol_classes.json")as f:
         #       dic = json.load(f)
         #    s = ""
         #    for i in idols:
         #       name = dic[i]
         #       s += name + "\n"
         #    s += "を検出しました"
         #    await message.reply(s)
         #    cv2.imwrite("yolov5/data/result/image.png", img)


def setup(bot):
   bot.add_cog(Main(bot))
