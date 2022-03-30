import asyncio
import json
import random
import glob
import os

import discord
from discord.ext import commands  # Bot Commands Frameworkのインポート
from gensim.models import KeyedVectors
from PIL import Image

from cog.util import file_download as pd
from cog.util.DbModule import DbModule as db
from cog.util import wiki_search
from cog.util import thread_webhook as webhook
from cog.util.picture_command import PicCtx
# コグとして用いるクラスを定義。


class Funny(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.tweet_wait = False
      self.stone = False
      self.db = db()
      self.picctx = PicCtx()
      self.kvs = KeyedVectors.load("text/jawiki.kv")

   @commands.command("教えて奈緒")
   async def wiki(self, ctx, word: str):
      """wikipediaを調べます。引数(単語)"""
      await ctx.send(wiki_search.wikipediaSearch(word))

   @commands.slash_command(name="rainbow", guild_ids=[os.getenv("FotM")])
   async def rainbow(self, ctx):
      """虹を出します"""
      await ctx.message.delete()
      await webhook.send(":heart: :orange_heart: :yellow_heart: :green_heart: :blue_heart: :purple_heart:", ctx)

   @commands.slash_command(name="rainbow2", guild_ids=[os.getenv("FotM")])
   async def rainbow2(self, ctx):
      """虹をたくさん出します"""
      emoji = ""
      await ctx.message.delete()
      with open("json/emoji.json", "r")as f:
         dic = json.load(f)
      for i in dic["rainbow_art"]:
         emoji += str(self.bot.get_emoji(int(i)))
      await webhook.send(emoji, ctx)

   @commands.slash_command(name="rainbow3", guild_ids=[os.getenv("FotM")])
   async def rainbow3(self, ctx):
      """虹をめちゃくちゃ出します"""
      emoji = ""
      await ctx.message.delete()
      with open("json/emoji.json", "r")as f:
         dic = json.load(f)
      text = dic["rainbow_art"]
      for i in range(7):
         for i in text:
            emoji += str(self.bot.get_emoji(int(i)))
         emoji += "\n"
         pop = text.pop(0)
         text.append(pop)
      await webhook.send(emoji, ctx)

   def paste(self, img_list):
      img_width = 0
      dst = Image.new('RGBA', (120 * len(img_list), 120))
      for img in img_list:

         img = img.resize((120, 120))
         dst.paste(img, (img_width, 0))
         img_width += img.width
      return dst

   def paste2(self, img_list):
      img_height = 0
      dst = Image.new('RGBA', (120, 120 * len(img_list)))
      for img in img_list:

         img = img.resize((120, 120))
         dst.paste(img, (0, img_height))
         img_height += img.height
      return dst

   @commands.command(aliases=["スタンプ", "b", "big"])
   async def stamp(self, ctx, *emoji: discord.Emoji):
      await ctx.message.delete()
      if len(emoji) < 2:
         url = emoji[0].url
         await webhook.send(url, ctx)
      else:
         for i, emoji in enumerate(emoji):
            pd.download_img(emoji.url, f"picture/emojis/emoji{i}.png")
         png_name = sorted(glob.glob('picture/emojis/*png'))
         im_list = []
         for file_name in png_name:
            Image_tmp = Image.open(file_name)
            im_list.append(Image_tmp)
         self.paste(im_list).save("picture/emojis/union_emoji.png")
         await webhook.send("", ctx, file=discord.File("picture/emojis/union_emoji.png"))
         for i in sorted(glob.glob('picture/emojis/*png')):
            os.remove(i)

   @commands.command(aliases=["d"])
   async def stamp2(self, ctx, *emoji: discord.Emoji):
      await ctx.message.delete()
      if len(emoji) < 2:
         url = emoji[0].url
         await webhook.send(url, ctx)
      else:
         for i, emoji in enumerate(emoji):
            pd.download_img(emoji.url, f"picture/emojis/emoji{i}.png")
         png_name = sorted(glob.glob('picture/emojis/*png'))
         im_list = []
         for file_name in png_name:
            Image_tmp = Image.open(file_name)
            im_list.append(Image_tmp)
         self.paste2(im_list).save("picture/emojis/union_emoji.png")
         await webhook.send("", ctx, file=discord.File("picture/emojis/union_emoji.png"))
         for i in sorted(glob.glob('picture/emojis/*png')):
            os.remove(i)

   @commands.command(aliases=["u", "unicode"])
   async def normal_emoji(self, ctx, emojis: str):
      try:
         emojis = f"{ord(emojis):x}"
         url = f"https://bot.mods.nyc/twemoji/{emojis}.png"
      except TypeError:
         await ctx.reply("その絵文字は対応していません、ごめんね")
         return
      await ctx.message.delete()
      await webhook.send(url, ctx)

   @commands.command("類似語")
   async def similar(self, ctx, word: str):
      wordlist = [x[0] for x in self.kvs.most_similar(positive=[word])]
      text = "\n".join(wordlist)
      await ctx.send(f"```{text}```")

   @commands.Cog.listener()
   async def on_message(self, message):
      if message.author.bot:
         return
      if "なおはじ" in message.content:
         emoji = [
             "<:na:681866058055024801>",
             "<:o_:681866075935211555>",
             "<:ha:681866087402700829>",
             "<:ji:681866097858969677>"]
         for i in emoji:
            await message.add_reaction(i)
      if "ｶﾐﾔﾅｵ" in message.content:
         emoji = [
             "<a:kamiya:714088347924168714>",
             "<a:unnamed:714091501646381058>",
             "<a:Nao_Loading_5:714091475444432917>",
             "<a:nao:714091488899891200>",
             "<a:1478254807_tHGkQDRV:714091363360047205>",
             "<a:1478254807_4CbzcReG:714091384411389952>",
         ]
         for i in emoji:
            await message.add_reaction(i)
      if "なおすき" in message.content:
         self.db.update('update naosuki_count set count=count+1')


def setup(bot):
   bot.add_cog(Funny(bot))
