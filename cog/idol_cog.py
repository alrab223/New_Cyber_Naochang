import json
import os
import random

import discord
import requests
from discord.ext import commands, pages


class Idol(commands.Cog):

   def __init__(self, bot):
      self.bot = bot

   @commands.slash_command(name="楽曲検索", guild_ids=[os.getenv("FotM")])
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
      with open("json/idol_data_moba.json")as f:
         cards = json.load(f)
      card = random.choice(cards["content"])
      embed = discord.Embed(title=f"{card['name']}")
      embed.set_image(url=f'https://lipps.pink-check.school/cardimage/withoutsign/{card["cardHash"]}')
      embed.add_field(name="コスト", value=f"{card['cost']}")
      embed.add_field(name="攻", value=f"{card['defaultAttack']}")
      embed.add_field(name="守", value=f"{card['defaultDefence']}")
      if card['abilityEffect']['effect'] != '':
         embed.add_field(name=f"特技「{card['abilityName']}」", value=f"{card['abilityEffect']['effect']}", inline=False)
      await ctx.send(embed=embed)

   @commands.slash_command(name="納税", guild_ids=[os.getenv("FotM")])
   async def tax(self, ctx):
      with open('json/idol_data.json', 'r')as f:
         idol_data = json.load(f)
      num = random.randint(1, 100)
      if num < 4:
         rarity = [x for x in idol_data['result'] if x['rarity_dep']['rarity'] == 7]
      elif num > 3 and num < 16:
         rarity = [x for x in idol_data['result'] if x['rarity_dep']['rarity'] == 5]
      else:
         rarity = [x for x in idol_data['result'] if x['rarity_dep']['rarity'] == 3]
      idol = random.choice(rarity)
      url = f'https://starlight.kirara.ca/api/v1/card_t/{idol["id"]}'
      r = requests.get(url)
      image_url = r.json()['result'][0]['card_image_ref']
      card_title = r.json()['result'][0]['name']
      embed = discord.Embed(title=card_title)
      embed.set_image(url=image_url)
      await ctx.respond(embed=embed)


def setup(bot):

   bot.add_cog(Idol(bot))
