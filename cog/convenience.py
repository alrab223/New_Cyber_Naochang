import asyncio
import json
import os
import re
import datetime

import discord
from discord.ext import commands

from cog.util.DbModule import DbModule as db
from cog.util import thread_webhook as webhook


class Convenience(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.db = db()
      with open("json/picture.json", "r") as f:
         self.colla_num = json.load(f)

   @commands.is_owner()
   @commands.command("ナオビーム")
   async def nao_beam(self, ctx, user: discord.Member, num: int):
      logs = []
      async for log in ctx.channel.history(limit=num):
         logs.append(log)
      await ctx.channel.delete_messages(logs)

   @commands.command()
   async def status(self, ctx, user: discord.Member = None):
      roles = []
      user = user or ctx.author
      embed = discord.Embed(title=user.name, color=0xC902FF)
      embed.set_thumbnail(url=user.avatar_url)
      embed.add_field(name="ユーザーID", value=user.id)
      embed.add_field(name="ニックネーム", value=user.display_name)
      joined_time = user.joined_at + datetime.timedelta(hours=9)
      embed.add_field(name="サーバー参加日", value=joined_time.strftime('%Y-%m-%d %H:%M:%S'), inline=False)
      joined_time = user.created_at + datetime.timedelta(hours=9)
      embed.add_field(name="ユーザー作成日", value=joined_time.strftime('%Y-%m-%d %H:%M:%S'))
      coin_have = self.db.select(f'select mayuge_coin from user_data where id={user.id}')[0]['mayuge_coin']
      embed.add_field(name="所持まゆげコイン枚", value=coin_have)
      roles = [x.name.replace('@', '') for x in user.roles]
      text = ",".join(roles)
      embed.add_field(name="ロール", value=text, inline=False)
      await ctx.send(embed=embed)

   @commands.is_owner()
   @commands.command("バックアップ")
   async def time_stone(self, ctx, copy_to: int):
      msg = []
      channel = self.bot.get_channel(copy_to)
      async for message in channel.history(limit=None):
         msg.append(message)
      msg.reverse()
      thread = ctx.guild.get_thread(ctx.channel.id)

      ch_webhooks = await ctx.channel.parent.webhooks()
      Channel_webhook = discord.utils.get(ch_webhooks, name="久川颯")

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

   @commands.command("vc通知")
   @commands.dm_only()
   async def vc_news(self, ctx, num: str):
      if num == "オフ":
         self.db.update(
             f'update vc_notification set vc_notification=0 where id={ctx.author.id}')
         await ctx.send(ctx.author.mention + "通知を解除しました")
      else:
         self.db.update(
             f'update vc_notification set members={num},vc_notification=1 where id={ctx.author.id}')
         await ctx.send(f"参加人数{num}以上で通知します")

   @commands.dm_only()
   @commands.command("予約投稿")
   async def future_send(self, ctx, time: str, channel_id: int):
      def user_check(message):
         return message.author.id == ctx.author.id
      await ctx.send("メッセージを入力してください")
      msg = await self.bot.wait_for('message', check=user_check)

      await ctx.send("この内容でいいですか？間違い無ければ「はい」と入力してください")

      def user_check2(message):
         return message.author.id == ctx.author.id and message.content == "はい"
      try:
         await self.bot.wait_for('message', check=user_check2)
      except asyncio.TimeoutError:
         return
      self.db.allinsert("future_send", [ctx.author.id, msg.content, time, channel_id, ctx.message.id])
      await ctx.send("予約が完了しました")

   @commands.dm_only()
   @commands.command("予約投稿確認")
   async def future_send_confirm(self, ctx):
      text = ''
      send_data = self.db.select(f'select * from future_send where id={ctx.author.id}')
      for count, data in enumerate(send_data, 1):
         channel = await self.bot.fetch_channel(data['channel_id'])
         text += f'{count},メッセージ: {data["text"]} \n時刻: {data["time"]} チャンネル名:{channel.name}\n\n'
      await ctx.send(f'```{text}```')
      await ctx.send('メッセージを取り消す場合は```!del```コマンドを使用してください')

   @commands.dm_only()
   @commands.command('del')
   async def delete_send(self, ctx):
      text = ''
      message_id = []
      send_data = self.db.select(f'select * from future_send where id={ctx.author.id}')
      for count, data in enumerate(send_data, 1):
         message_id.append(data['message_id'])
         channel = await self.bot.fetch_channel(data['channel_id'])
         text += f'{count},メッセージ: {data["text"]} \n時刻: {data["time"]} チャンネル名:{channel.name}\n\n'
      await ctx.send(f'```{text}```')
      await ctx.send('取り消したいメッセージの番号を書き込んでください')

      def user_check(message):
         return message.author.id == ctx.author.id and message.content.isdigit() is True
      msg = await self.bot.wait_for('message', check=user_check)
      self.db.update(f"delete from future_send where message_id={message_id[int(msg.content)-1]}")
      await ctx.send('消去しました')

   @commands.Cog.listener()
   async def on_message(self, message):
      if message.author.bot:
         return
      pattern = "https?://[\\w/:%#\\$&\\?\\(\\)~\\.=\\+\\-]+"
      text: list = re.findall(pattern, message.content)
      ch_list: list = ["Chat_ch1", "Chat_ch2"]
      channels: list = []
      for i in ch_list:
         channels.append(self.bot.get_channel(int(os.environ.get(i))))
      if message.channel.id == channels[0].id or message.channel.id == channels[1].id:
         for channel in channels:
            async for log in channel.history(limit=40):
               url_list: list = re.findall(pattern, log.content)
               if set(text) & set(url_list) and message.id != log.id:
                  msg = await message.channel.send(f"{message.author.mention}{channel.name}に同じURLがもう貼られてるよ！")
                  await asyncio.sleep(10)
                  await msg.delete()
                  return


def setup(bot):
   bot.add_cog(Convenience(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。
