import asyncio
import random
import datetime
import os
import re

import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText

from cog.util.DbModule import DbModule as db
from cog.util import thread_webhook as webhook


class Slash(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.tweet_wait = False
      self.stone = False
      self.db = db()

   @commands.has_role("スタッフ")
   @commands.slash_command(guild_ids=[os.getenv("FotM")])
   async def button(self, ctx):
      button = Button(label="test", style=discord.ButtonStyle.green,)

      async def call(interaction):
         await interaction.response.send_message("Hi")
      view = View()
      button.callback = call
      view.add_item(button)
      await ctx.send("あい", view=view)

   def quickpick_process(self, ticket: str, starters: int):
      horse = range(1, starters + 1)
      if ticket == "単勝,複勝":
         vote = random.sample(horse, 1)
      elif ticket == "馬連":
         vote = sorted(random.sample(horse, 2))
      elif ticket == "馬単":
         vote = random.sample(horse, 2)
      elif ticket == "ワイド":
         vote = sorted(random.sample(horse, 2))
      elif ticket == "3連複":
         vote = sorted(random.sample(horse, 3))
      else:  # 3連単の時
         vote = random.sample(horse, 3)
      vote = [str(i) for i in vote]
      vote = "→".join(vote)
      return vote

   @commands.slash_command(name="クイックピック", guild_ids=[os.getenv("FotM")])
   async def quickpick(self, ctx, starters: int):
      '''頭数を選択してクイックピック！'''
      comp = []
      comp2 = []
      ticket = ["単勝,複勝", "馬連", "馬単", "ワイド", "3連複", "3連単"]
      for i, name in enumerate(ticket):
         if i < 5:
            comp.append(Button(label=name, style=discord.ButtonStyle.green, custom_id=name,))
         else:
            comp2.append(Button(label=name, style=discord.ButtonStyle.green, custom_id=name,))

      async def call(interaction):
         vote = self.quickpick_process(interaction.data["custom_id"], starters)
         vote = f"{interaction.data['custom_id']}\n{vote}"
         await interaction.response.send_message(content=vote, ephemeral=True)

      view = View()
      for button in comp:
         button.callback = call
         view.add_item(button)
      for button in comp2:
         button.callback = call
         view.add_item(button)
      await ctx.respond("買え", view=view)
   
   @commands.has_role("スタッフ")
   @commands.slash_command(name="バックアップ", guild_ids=[os.getenv("FotM")])
   async def backup(self, ctx, copy_to: int):
      '''チャンネル丸ごとバックアップ！(スタッフ専用)'''
      msg = []
      channel = self.bot.get_channel(copy_to)
      async for message in channel.history(limit=None):
         msg.append(message)
      msg.reverse()
      thread = ctx.guild.get_thread(ctx.channel.id)

      ch_webhooks = await ctx.channel.parent.webhooks()
      Channel_webhook = discord.utils.get(ch_webhooks, name="naochang")

      for i in msg:
         payload = {
             "username": i.author.display_name,
             "content": i.content,
         }
         if i.author.avatar is None:
            payload["avatar_url"] = i.author.default_avatar.url
         else:
            payload["avatar_url"] = i.author.avatar.url
         if i.attachments:
            if ".mp4" in i.attachments[0].url:
               payload["content"] = "\n" + i.attachments[0].url
            else:
               payload["embeds"] = [{"image": {"url": i.attachments[0].url}}]

         code = webhook.send(payload, Channel_webhook.url, thread.id)
         while code != 200:
            print(f"エラー{code}")
            await asyncio.sleep(5)
            code = webhook.send(payload, Channel_webhook.url, thread.id)

         await asyncio.sleep(2)

   @commands.Cog.listener()
   async def on_application_command_error(self, ctx, error):
      if isinstance(error, (commands.MissingRole, commands.MissingAnyRole, commands.CheckFailure)):
         await ctx.send("権限がありません")
      else:
         print(error)


def setup(bot):
   bot.add_cog(Slash(bot))
