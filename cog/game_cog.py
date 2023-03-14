import asyncio
import glob
import json
import os
import random

import discord
from discord.ext import commands

from cog.util.DbModule import DbModule as db


class Game(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.handbattle = False
      self.slot = False
      self.chance = False
      self.db = db()

   @commands.command("")
   async def emoji(self, ctx):
      emoji = await ctx.guild.fetch_emojis()
      for i in emoji:
         print(i)

   async def bonus_slot(self, ctx, ei, judge, msg, slot_title, slot_num, debug=False, etc=False):
      count = 0
      for i, element in enumerate(ei):
         if judge[i] == element:
            count += 1

      if ((count == slot_num - 2 or count == slot_num - 1) and
              random.randint(1, slot_num) == 1) or debug:
         self.chance = True
         gif = await ctx.send("チャンス発生！！", file=discord.File("picture/bonus/triad.gif"))

         await msg.delete()
         await asyncio.sleep(3.5)
         await gif.delete()
         gif = await ctx.send(file=discord.File("picture/bonus/yattemiyo.gif"))
         for j in range(4):
            judge = []
            emoji = ""
            _, msg = await self.slot_maker(ctx, ['picture/bonus/yattemiyo.gif'], slot_title, slot_num, True)
            for i in range(slot_num):
               if i < slot_num - 2:
                  ran = ei[i]
               elif j == 3 and i == slot_num - 2:
                  ran = ei[i]
               else:
                  ran = random.choice(ei)
               judge.append(ran)
               emoji += str(self.bot.get_emoji(ran))
               if j == 3:
                  await msg.edit(content=emoji)
                  await asyncio.sleep(0.3)
            if j == 3:
               await asyncio.sleep(1)
               await gif.delete()
               if ei == judge:
                  return msg
               else:
                  return False

            await msg.edit(content=emoji)
            await asyncio.sleep(1)
            if ei == judge:
               return msg
            if j == 3:
               await gif.delete()
            await msg.delete()
      else:
         return False

   async def slot_maker(self, ctx, num, slot, count, bonus=False):
      emoji = ""
      for i in range(count):
         emoji += str(self.bot.get_emoji(int(os.environ.get(slot))))
      if num == 1:
         msg = await ctx.send(emoji)
         return msg
      else:
         if bonus:
            gif = False
         else:
            gif = await ctx.send(file=discord.File(random.choice(num)))
         msg = await ctx.send(emoji)
         await asyncio.sleep(3)
         return gif, msg

   async def slot_setup(self, ctx, slot_name: str, debug=False):  # スロットが遊べるかを確認する関数
      if self.slot is True:
         return False
      else:
         self.slot = True
      if slot_name == "NAOSUKI_SLOT":  # なおすきスロットの場合、その日にスロットを回してないか確認
         flag_list = self.db.select(f'select naosuki from user_data where id={ctx.author.id}')[0]
         if flag_list['naosuki'] == 1:
            await ctx.reply("なおすきスロット,スーパーなおすきスロットは1日一回までだよ！")
            return False
         else:
            self.db.update(f'update user_data set naosuki=1 where id={ctx.author.id}')
            return True
      else:
         with open('json/slot_data.json', 'r')as f:  # スロットの種類と使用コイン数を取得
            slot_data = json.load(f)
         flag_list = self.db.select(f'select mayuge_coin from user_data where id={ctx.author.id}')[0]
         if flag_list['mayuge_coin'] >= slot_data[slot_name]:  # 条件を満たせばコインを消費
            self.db.update(f'update user_data set mayuge_coin=mayuge_coin-{slot_data[slot_name]} where id={ctx.author.id}')
            return flag_list['mayuge_coin'] - slot_data[slot_name]  # 現在の所持コイン数を返す
         else:
            await ctx.reply(f"まゆげコインが足りません。コインが{slot_data[slot_name]}枚必要です")
            return False

   @commands.slash_command(name="なおすきスロット")
   async def naosuki_slot(self, ctx, debug=False):
      """スロットで遊びます。「なおすき」を揃えよう！(1日1回)"""
      if await self.slot_setup(ctx, "NAOSUKI_SLOT", debug) is False:  # スロットが遊べるかを判別する
         self.slot = False
         return
      await ctx.respond("スロット開始!")
      with open("json/emoji.json", "r") as f:  # リールを読み出す
         emdic = json.load(f)
      target = emdic["naosuki"]  # 当たりリールを保存する変数
      path = "picture/gif/slot/*.gif"
      num = glob.glob(path)
      gif, msg = await self.slot_maker(ctx, num, "naosuki_emoji", 4)
      judge = []  # 全リールを保存するリスト
      reel: str = ''  # リールを保存する変数
      for i in range(4):
         ran = random.choice(target)
         judge.append(ran)
         reel += str(self.bot.get_emoji(ran))
         await asyncio.sleep(0.3)
         await msg.edit(content=reel)
      # 当たった時の処理
      if target == judge:
         reel = emdic["nao_gif"]
         for i in reel:
            ej = str(self.bot.get_emoji(i))
            await msg.add_reaction(ej)
         await ctx.send(f"{ctx.author.mention}なおすき！なおすき！なおすき！")
      await gif.delete()
      self.slot = False

   @commands.slash_command(name="レインボースロット", guild_ids=[os.getenv("FotM")])
   async def side(self, ctx, debug=False):
      """スロットで遊びます"""

      coin = await self.slot_setup(ctx, "RAINBOW_SLOT", debug)
      if not coin:
         self.slot = False
         return
      await ctx.respond("スロット開始!")
      log = await ctx.send(f"{ctx.author.mention}残り{coin}まゆげコイン")
      with open("json/emoji.json", "r") as f:
         emdic = json.load(f)
      emoji = ""
      judge = []
      ei = emdic["2ndSIDE"]

      for i in emdic["rainbow_art"]:
         emoji += str(self.bot.get_emoji(int(i)))
      rainbow1 = await ctx.send(emoji)
      msg = await self.slot_maker(ctx, 1, "2ndSIDE", 7)
      rainbow2 = await ctx.send(emoji)
      await asyncio.sleep(3)
      emoji = ""
      if random.randint(1, 1000) == 70:
         sp_emoji = emdic["2ndSIDE"]
         for i in sp_emoji:
            emoji += str(self.bot.get_emoji(i))
         await msg.edit(content=emoji)
      else:
         for i in range(7):
            ran = random.choice(ei)
            judge.append(ran)
            emoji += str(self.bot.get_emoji(ran))
         await msg.edit(content=emoji)
         answer = await self.bonus_slot(ctx, ei, judge, msg, '2ndSIDE', 7, debug)
         if ei == judge or answer:
            msg = answer
            emoji = emdic["nao_gif"]
            for i in emoji:
               ej = str(self.bot.get_emoji(i))
               await msg.add_reaction(ej)
            await ctx.send(f"{ctx.author.mention}虹色橋が完成した")
      await rainbow1.delete()
      await rainbow2.delete()
      await log.delete()
      self.slot = False

   @commands.slash_command(name="神谷奈緒チャレンジ", guild_ids=[os.getenv("FotM")])
   async def hours24_slot(self, ctx, debug=False):
      """スロットで遊びます"""
      coin = await self.slot_setup(ctx, "NAO_CHALLENGE", debug)
      if not coin:
         self.slot = False
         return
      await ctx.respond("チャレンジ開始!")
      log = await ctx.send(f"{ctx.author.mention}残り{coin}まゆげコイン")

      with open("json/emoji.json", "r") as f:
         emdic = json.load(f)
      emoji = ""
      judge = []
      ei = emdic["kamiyanao"]
      path = "picture/gif/slot/*.gif"
      num = glob.glob(path)
      gif, msg = await self.slot_maker(ctx, num, "kamiyanao_slot", 5)
      emoji = ""
      for i in range(5):
         ran = random.choice(ei)
         judge.append(ran)
         emoji += str(self.bot.get_emoji(ran))
         await asyncio.sleep(0.1)
         await msg.edit(content=emoji)
      answer = await self.bonus_slot(ctx, ei, judge, msg, "kamiyanao_slot", 5, debug)
      if answer and answer is True:
         msg = answer
      if ei == judge or answer:
         emoji = emdic["nao_gif"]
         emoji += emdic["kamiyanao"]
         emoji += emdic["naosuki"]
         for i in emoji:
            ej = str(self.bot.get_emoji(i))
            try:
               await msg.add_reaction(ej)
            except AttributeError:
               pass
         await ctx.send(f"{ctx.author.mention}チャレンジ成功！！")
      await gif.delete()
      await log.delete()
      self.slot = False

   @commands.slash_command(name="連続神谷奈緒チャレンジ", guild_ids=[os.getenv("FotM")])
   async def con_hours24_slot(self, ctx):
      """神谷奈緒チャレンジ5連打!"""
      coin = await self.slot_setup(ctx, "NAO_CHALLENGE5")
      if not coin:
         self.slot = False
         return
      log = await ctx.send(f"{ctx.author.mention}残り{coin}まゆげコイン")
      await ctx.respond("チャレンジ開始!")
      with open("json/emoji.json", "r") as f:
         emdic = json.load(f)
      emoji = ""
      judge = []
      ei = emdic["kamiyanao"]
      path = "picture/gif/slot/*.gif"
      num = glob.glob(path)
      for j in range(5):
         for i in range(5):
            emoji += str(self.bot.get_emoji(751709132087754763))
         emoji += "\n"
      gif = await ctx.send(file=discord.File(random.choice(num)))
      msg = await ctx.send(emoji)
      await asyncio.sleep(1)

      emoji = ""
      moji = ""
      tmp = []
      moji2 = [[], [], [], [], []]
      for j in range(5):
         judge.append(random.choice(ei) for i in range(5))
      for j in range(5):
         tmp.append([str(self.bot.get_emoji(i)) for i in judge[j]])

      ran = []
      for j in range(5):
         ran.append([x[j] for x in tmp])
      for i in ran:
         for j in range(5):
            moji2[j % 5].append(i[j])

         for i in range(5):
            moji += "".join(moji2[i]) + "\n"
         await msg.edit(content=moji)
         await asyncio.sleep(0.1)
         moji = ""

      for i in judge:
         if ei == i:
            emoji = emdic["nao_gif"]
            emoji += emdic["kamiyanao"]
            emoji += emdic["naosuki"]
            for i in emoji:
               ej = str(self.bot.get_emoji(i))
               await msg.add_reaction(ej)
            await ctx.send(f"{ctx.author.mention}チャレンジ成功！！")
            self.chance = True
            break

      await gif.delete()
      await log.delete()
      self.slot = False


def setup(bot):
   bot.add_cog(Game(bot))
