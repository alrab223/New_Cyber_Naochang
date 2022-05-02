import csv
import json
import os
import random

import discord
import requests
from discord.ext import commands, pages
from cog.util import thread_webhook as webhook


class Idol(commands.Cog):

   def __init__(self, bot):
      self.bot = bot

   @commands.slash_command(name="楽曲検索", guild_ids=[os.getenv("FotM"), os.getenv("Jikken_Guild")])
   async def song_search(self, ctx, name: str):
      songs = requests.get("https://cgapi.krone.cf/v1/songs").json()
      status = {}
      for song in songs:
         for actor in song["artists"]:
            if actor == name:
               status[song["title"]] = song["artists"]
      if status == {}:
         await ctx.respond("指定のアイドルは存在しないようです")
      else:
         text = ""
         for i in status:
            artists = ",".join(status[i])
            text += i + "\n(" + artists + ")\n"
         text = "```" + text + "```"
         await ctx.respond(text)

   @commands.command("ユニット検索")
   async def unit_search(self, ctx, *args):
      flag = 0
      count = 0
      embed1 = discord.Embed(description='ユニット名一覧 1')
      embed2 = discord.Embed(description='ユニット名一覧 2')
      embed3 = discord.Embed(description='ユニット名一覧 3')
      embed4 = discord.Embed(description='ユニット名一覧 4')
      pages1 = [embed1, embed2, embed3, embed4]
      pages2 = []
      pagesj = [False, False, False, False]
      with open("json/unit_kai.json", "r", encoding="utf_8_sig") as f:
         dic = json.load(f)
      for i in dic["results"]["bindings"]:
         for j in list(args):
            if j in i["メンバー"]["value"]:
               flag += 1
            else:
               break
            if flag == len(list(args)):
               if count < 6:
                  embed1.add_field(name=i["ユニット名"]["value"], value=i["メンバー"]["value"], inline=False)
                  pagesj[0] = True
               elif count < 12:
                  pagesj[1] = True
                  embed2.add_field(name=i["ユニット名"]["value"], value=i["メンバー"]["value"], inline=False)
               elif count < 18:
                  pagesj[2] = True
                  embed3.add_field(name=i["ユニット名"]["value"], value=i["メンバー"]["value"], inline=False)
               else:
                  pagesj[3] = True
                  embed4.add_field(name=i["ユニット名"]["value"], value=i["メンバー"]["value"], inline=False)
               count += 1
         flag = 0
      for i in range(4):
         if pagesj[i]:
            pages2.append(pages1[i])
      paginator = pages.Paginator(pages=pages2)
      await paginator.send(ctx)

   @commands.command("ガシャ")
   async def gasya(self, ctx):
      with open('text/newcard.csv')as f:
         reader = csv.reader(f)
         l = [row for row in reader]
         l = random.choice(l)
         embed = discord.Embed(title=f"{l[3]}")
         embed.set_image(url=f'https://pink-check.school/image/withoutsign/{l[1]}')
         embed.add_field(name="コスト", value=f"{l[15]}")
         embed.add_field(name="攻", value=f"{l[18]}")
         embed.add_field(name="守", value=f"{l[19]}")
         if l[21] != '':
            embed.add_field(name=f"特技「{l[20]}」", value=f"{l[21]}", inline=False)
         await ctx.send(embed=embed)

   @commands.command("納税")
   async def tax(self, ctx):
      webhooks = await webhook.get_webhook(ctx)
      webhook_url = webhooks.url
      urls = []
      with open('json/idol_data.json', 'r')as f:
         idol_data = json.load(f)
      num = random.randint(1, 100)
      if num < 4:
         ssr = [x for x in idol_data['result'] if x['rarity_dep']['rarity'] == 5]
      elif num > 3 and num < 16:
         ssr = [x for x in idol_data['result'] if x['rarity_dep']['rarity'] == 4]
      else:
         ssr = [x for x in idol_data['result'] if x['rarity_dep']['rarity'] == 3]
      idol = random.choice(ssr)
      url = f'https://starlight.kirara.ca/api/v1/card_t/{idol["id"]}'
      r = requests.get(url)
      urls.append(r.json()['result'][0]['card_image_ref'])

      webhook_c.image_add(urls)
      webhook_c.add_title(title=r.json()['result'][0]['name'])
      webhook_c.webhook_send(webhook_url)

   @commands.command("カード検索")
   async def cards(self, ctx, name: str):
      card_list = []
      card_list_evolution = []
      with open('text/newcard.csv')as f:
         reader = csv.reader(f)
         l = [row for row in reader]
         for card in l:

            if name == card[6]:
               card_list = []
               card_list.append(card[3])
               card_list_evolution.append(card[3] + '+')
               break
            elif name in card[3] and card[3][-1] != '+':
               card_list.append(card[3])
            elif name in card[3] and card[3][-1] == '+':
               card_list_evolution.append(card[3])
         print(card_list, card_list_evolution)

         if len(card_list) > 10:
            await ctx.send('該当カードが多いのでもう少し絞ってね')
         elif len(card_list) > 1:
            embed = discord.Embed(title="複数見つかりました", description="選んでください")
            for card in card_list:
               embed.add_field(name="カード名", value=f"{card}")
            await ctx.send(embed=embed)

         elif len(card_list) == 1:
            card = [x for x in l if x[3] == card_list[0]][0]
            card2 = [x for x in l if x[3] == card_list_evolution[0]][0]
            webhook = await self.get_webhook(ctx)
            webhook_url = webhook.url
            webhook_c = Webhook_Control()
            urls = [
                f'https://pink-check.school/image/withoutsign/{card[1]}',
                f'https://pink-check.school/image/withoutsign/{card2[1]}']
            webhook_c.image_add(urls)
            webhook_c.add_title(title=f"{card[3]},{card2[3]}")
            webhook_c.add_field(name="コスト", value=f"{card[15]}")
            webhook_c.add_field(name="攻", value=f"{card[18]}")
            webhook_c.add_field(name="守", value=f"{card[19]}")
            if card[21] != '':
               webhook_c.add_field(name="特技「{card[20]}」", value=f"{card[21]}", inline=False)
            webhook_c.add_field(name="コスト", value=f"{card2[15]}")
            webhook_c.add_field(name="攻", value=f"{card2[18]}")
            webhook_c.add_field(name="守", value=f"{card2[19]}")
            if card2[21] != '':
               webhook_c.add_field(name=f"特技「{card2[20]}」", value=f"{card2[21]}", inline=False)
            webhook_c.webhook_send(webhook_url)
         else:
            await ctx.send("見つかりませんでした")

# Bot本体側からコグを読み込む際に呼び出される関数。


def setup(bot):

   bot.add_cog(Idol(bot))  # TestCogにBotを渡してインスタンス化し、Botにコグとして登録する。
