import asyncio
import os
import re
import datetime

import discord
from discord.ext import commands

from cog.util.DbModule import DbModule as db
from cog.util import file_download as pd


class Convenience(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.db = db()

   @commands.is_owner()
   @commands.command("ナオビーム")
   async def nao_beam(self, ctx, num: int):
      logs = []
      async for log in ctx.channel.history(limit=num):
         logs.append(log)
      user_logs = [x for x in logs]
      await ctx.channel.delete_messages(user_logs)

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
   @commands.slash_command(name="予約投稿")
   async def future_send(self, ctx, time: str, channel_id: str):
      """日付の指定は(yyyy/mm/dd-hh:mm)の形式でお願いします"""
      def user_check(message):
         return message.author.id == ctx.author.id
      await ctx.send("メッセージを入力してください")
      msg = await self.bot.wait_for('message', check=user_check)

      def attachments_check(message):
         if message.author.id == ctx.author.id and message.content == "進む":
            return True
         elif message.attachments:
            return True
         else:
            False

      await ctx.send("画像の添付が必要な場合はここで貼ってください。必要なければ「進む」と入力してください")
      picture = await self.bot.wait_for('message', check=attachments_check)
      if picture.attachments:
         attachments = picture.attachments[0].url
         text = msg.content + "\n" + attachments

      await ctx.send("この内容でいいですか？間違い無ければ「はい」と入力してください")

      def user_check2(message):
         return message.author.id == ctx.author.id and message.content == "はい"
      try:
         await self.bot.wait_for('message', check=user_check2)
      except asyncio.TimeoutError:
         await ctx.send("エラーが発生しました")
         return
      self.db.allinsert("future_send", [ctx.author.id, text, time, int(channel_id), msg.id])
      await ctx.send("予約が完了しました")

   @commands.dm_only()
   @commands.slash_command(name="予約投稿確認")
   async def future_send_confirm(self, ctx):
      text = ''
      send_data = self.db.select(f'select * from future_send where id={ctx.author.id}')
      for count, data in enumerate(send_data, 1):
         channel = await self.bot.fetch_channel(data['channel_id'])
         text += f'{count},メッセージ: {data["text"]} \n時刻: {data["time"]} チャンネル名:{channel.name}\n\n'
      await ctx.respond(f'```{text}```')
      await ctx.respond('メッセージを取り消す場合は```!del```コマンドを使用してください')

   @ commands.dm_only()
   @ commands.command('del')
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

   # 話題の重複を防ぐ
   @ commands.Cog.listener()
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
   bot.add_cog(Convenience(bot))
