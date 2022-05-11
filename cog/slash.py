import asyncio
import random
import os
import re

import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, InputText

from cog.util.DbModule import DbModule as db
from cog.util import tweet_stream
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

   @commands.has_role("スタッフ")
   @commands.slash_command(guild_ids=[os.getenv("FotM")])
   async def modals(self, ctx):

      async def call(interaction):
         await interaction.response.send_message(f'Thanks for your response, {name}!', ephemeral=True)
      modal = Modal("a_modal")

      name = InputText(label='Name', placeholder="default")
      answer = InputText(label='Answer', style=discord.InputTextStyle.paragraph)
      name.callback = call
      answer.callback = call
      modal.add_item(name)
      modal.add_item(answer)
      await ctx.interaction.response.send_modal(modal)

   async def tweet_send(self, ctx):
      while self.db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"] == 1:
         try:
            tweet = self.db.select("select *from Twitter_log limit 1")[0]
            self.db.auto_delete("Twitter_log", {"tweet_id": tweet["tweet_id"]})
         except IndexError:
            await asyncio.sleep(2)
            continue
         urls = []
         medias = ["media1", "media2", "media3", "media4"]
         for media in medias:
            if tweet[media] is not None:
               urls.append(tweet[media])
            else:
               break
         pattern = "https?://[\\w/:%#\\$&\\?\\(\\)~\\.=\\+\\-]+"
         url_flag: list = re.findall(pattern, tweet["text"])
         if url_flag != []:
            tweet["text"] = re.sub(pattern, "", tweet["text"])
            tweet["text"] += "```\nURLが含まれているツイートです。URL先で確認して下さい```"

         payload = webhook.payload_edit(tweet["user"], tweet["icon"], tweet["text"], urls)
         url = f"https://twitter.com/{tweet['screen_id']}/status/{tweet['tweet_id']}"
         payload["embeds"].append({"title": "ツイート先に飛ぶ", "url": url})
         Ch_webhook = await webhook.get_webhook(ctx)
         webhook.custom_send(payload, Ch_webhook.url, ctx)
         await asyncio.sleep(2)

   @commands.has_role("スタッフ")
   @commands.slash_command(name="ツイート取得", guild_ids=[os.getenv("FotM")])
   async def tweet_get(self, ctx, word: str):
      """ツイートを取得してここに垂れ流します(スタッフ専用)"""
      if self.db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"] == 1:
         await ctx.send("すでにこの機能が使用されているため、現在使えません")
         return
      self.db.update("delete from Twitter_log")
      tweet_stream.main(word)
      self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "tweet_get"})
      await ctx.respond(f"{word}でツイート取得を開始します")
      await self.tweet_send(ctx)

   @commands.has_role("スタッフ")
   @commands.slash_command(name="ツイート取得停止", guild_ids=[os.getenv("FotM")])
   async def tweet_get_stop(self, ctx):
      """ツイート取得を停止します"""
      self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "tweet_get"})
      await ctx.respond("ツイート取得を停止しました")

   @commands.Cog.listener()
   async def on_application_command_error(self, ctx, error):
      if isinstance(error, (commands.MissingRole, commands.MissingAnyRole, commands.CheckFailure)):
         await ctx.send("権限がありません")
      else:
         print(error)


def setup(bot):
   bot.add_cog(Slash(bot))
