import json
import os
import random

import discord
import requests
from discord.ext import commands, pages


class Idol(commands.Cog):

   def __init__(self, bot):
      self.bot = bot

   @commands.slash_command(name="楽曲検索")
   async def song_search(self, ctx, name: str):
      songs = requests.get("https://cgapi.krone.cf/v1/songs").json()
      status = {}
      for song in songs:
         for actor in song["artists"]:
            if actor == name:
               status[song["title"]] = song["artists"]
      if status == {}:
         await ctx.respond("存在しないようです")
      else:
         text = ""
         for i in status:
            artists = ",".join(status[i])
            text += i + "\n(" + artists + ")\n"
         text = "```" + text + "```"
         await ctx.respond(text)

   
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
