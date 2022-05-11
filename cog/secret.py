import csv
import json

import discord
from discord.ext import commands

from cog.util import thread_webhook as webhook


class Secret(commands.Cog):

   def __init__(self, bot):
      self.bot = bot

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


def setup(bot):

   bot.add_cog(Secret(bot))
