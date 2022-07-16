import asyncio
import random
import os
import re
import datetime

import requests

import discord
from discord.ext import commands

from cog.util.DbModule import DbModule as db


class Announce(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.db = db()

   @commands.slash_command(name="モバマスボーダー通知")
   async def moba_border_announce(self, ctx):
      flag = self.db.select("select * from flag_control where flag_name='moba_border_announce'")[0]["flag"]
      if flag == 0:
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "moba_border_announce"})
         self.db.allinsert("channel_flag_control", [None, ctx.channel.id, "moba_border_announce"])
         await ctx.respond("このスレッドでボーダーを通知します")
      else:
         self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "moba_border_announce"})
         self.db.auto_delete("channel_flag_control", {"flag_name": "moba_border_announce"})
         await ctx.respond("ボーダー通知を終了します")


def setup(bot):
   bot.add_cog(Announce(bot))
