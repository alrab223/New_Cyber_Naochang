import asyncio
import datetime
import glob
import json
import os
import random
import traceback
from re import M

import discord
import gspread
import requests
import urllib3
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord.ui import Button, InputText, Modal, View

from cog.util.DbModule import DbModule as db


class Time(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.birthday_sned = False
      self.flag = 1
      self.weather_list = []
      self.time_process.start()
      self.event = False  # 特殊イベントの時のみTrue
      self.db = db()

   def weather_get(self):  # 天気取得
      self.weather_list = []
      tokyo = 'https://weather.yahoo.co.jp/weather/jp/13/4410.html'
      osaka = "https://weather.yahoo.co.jp/weather/jp/27/6200.html"
      hokkaido = "https://weather.yahoo.co.jp/weather/jp/1b/1400.html"
      hukuoka = "https://weather.yahoo.co.jp/weather/jp/40/8210.html"
      weather_lists = [tokyo, osaka, hokkaido, hukuoka]
      name = ["東京", "大阪", "北海道", "福岡"]
      http = urllib3.PoolManager()
      for i, j in enumerate(weather_lists):
         instance = (http.request('GET', j))
         soup = BeautifulSoup(instance.data, 'html.parser')
         tenki_today = soup.select_one('#main > div.forecastCity > table > tr > td > div > p.pict')
         try:
            text = tenki_today.text.replace("今日の天気は", "")
            self.weather_list.append(f"{name[i]}の天気:{text}")
         except AttributeError:
            pass

   @tasks.loop(seconds=5.0)
   async def bot_status_changer(self):  # botのステータス欄を更新
      if self.flag == 1:
         count = self.db.select('select count from naosuki_count')[0]
         text = "カウント:" + str(count["count"])
         await self.bot.change_presence(activity=discord.Game(name=text))
         self.flag += 1
      elif self.flag == 2:
         try:
            await self.bot.change_presence(activity=discord.Game(name=self.weather_list[0]))
            num = self.weather_list.pop(0)
            self.weather_list.append(num)
         except IndexError:
            pass
         self.flag += 1
      else:
         guild = self.bot.get_guild(int(os.environ.get("FotM")))
         user_count = sum(1 for member in guild.members if not member.bot)
         await self.bot.change_presence(activity=discord.Game(name=f"現在のメンバー数:{user_count-4}"))
         self.flag = 1

   def daily_pic(self):
      with open('json/idol_data.json', 'r')as f:
         idol_data = json.load(f)
      idols = [x for x in idol_data['result'] if x['name_only'] == "神谷奈緒"]
      ids = [x['id'] for x in idols]
      ids += [x['id'] + 1 for x in idols]
      id = random.choice(ids)
      url = f'https://starlight.kirara.ca/api/v1/card_t/{id}'
      r = requests.get(url)
      url = r.json()['result'][0]['card_image_ref']
      return url

   def get_idol_pic(self, name):
      with open('json/idol_data.json', 'r')as f:
         idol_data = json.load(f)
      idols = [x for x in idol_data['result'] if x['name_only'] == name]
      ids = [x['id'] + 1 for x in idols if x["rarity_dep"]["rarity"] == 7]
      id = random.choice(ids)
      url = f'https://starlight.kirara.ca/api/v1/card_t/{id}'
      r = requests.get(url)
      url = r.json()['result'][0]['spread_image_ref']
      return url

   def birthday(self):
      birthday_idol = []
      nowtime = datetime.datetime.now()
      idols = self.db.select("select * from idol_data")
      for idol in idols:
         month = int(idol["birthday"].split("/")[0])
         day = int(idol["birthday"].split("/")[1])
         if nowtime.month == month and nowtime.day == day:
            birthday_idol.append(idol["name"])
      return birthday_idol

   async def daily_process(self):
      if self.event:
         await self.special_daily()
      else:
         self.db.update('update user_data set mayuge_coin=mayuge_coin+3,naosuki=0')
         self.weather_get()
         channel = self.bot.get_channel(int(os.environ.get("naosuki_ch")))
         url = self.daily_pic()
         await channel.send(url)
         await channel.send("コインを追加しました")
         emoji = ""
         with open("json/emoji.json", "r")as f:
            dic = json.load(f)
         for i in dic["rainbow_art"]:
            emoji += str(self.bot.get_emoji(int(i)))
         await channel.send(emoji)

      # 誕生日処理
      channel = self.bot.get_channel(int(os.environ.get("Chat_ch1")))
      birthday_idol = self.birthday()  # 誕生日を取得
      for idol in birthday_idol:
         url = self.get_idol_pic(idol)  # 画像を取得
         await channel.send(f"今日は{idol}さんの誕生日です。祝おう！")
         msg = await channel.send(url)
         await msg.add_reaction("🎂")

      # 記念日処理
      channel = self.bot.get_channel(int(os.environ.get("Chat_ch2")))
      gc = gspread.service_account(filename="json/key.json")
      sh = gc.open("記念日一覧").sheet1
      data_list = sh.get_all_values()
      now = datetime.datetime.now()
      day = f"{now.month}/{now.day}"
      for i in data_list[1::]:
         if i[0] == day:
            text = f"今日は{i[1]}です。\n{i[2]}"
            await channel.send(text)
            if i[3] != "":
               await channel.send(i[3])

   async def reservation_message_check(self, nowtime):  # 予約投稿の処理を行う
      messages = self.db.select("select * from future_send")
      for message in messages:
         print(f"{nowtime.year}/{str(nowtime.month).zfill(2)}/{str(nowtime.day).zfill(2)}-{str(nowtime.hour).zfill(2)}:{str(nowtime.minute).zfill(2)}")
         if message['time'] == f"{nowtime.year}/{str(nowtime.month).zfill(2)}/{str(nowtime.day).zfill(2)}-{str(nowtime.hour).zfill(2)}:{str(nowtime.minute).zfill(2)}":
            user = await self.bot.fetch_user(message['id'])
            channel = self.bot.get_channel(message['channel_id'])
            ch_webhooks = await channel.webhooks()
            hook = discord.utils.get(ch_webhooks, name="naochang")
            if hook is None:
               hook = await channel.create_webhook(name="naochang")
            await hook.send(content=message['text'],
                            username=user.name,
                            avatar_url=user.avatar.url)
            self.db.auto_delete("future_send", {"message_id": message["message_id"]})

   async def make_graph(self, event_score, ranks):
      x = []
      for border_time in event_score["content"]:
         border_time = border_time["time"].replace(":00+09:00", "")
         border_time = border_time.replace("T", "")
         x.append(border_time)

   @tasks.loop(seconds=60.0)
   async def time_process(self):
      nowtime = datetime.datetime.now()
      if nowtime.hour == 23 and nowtime.minute == 59:
         wait_seconds = 60.0 - float(nowtime.second)
         await asyncio.sleep(wait_seconds)
         await self.daily_process()

      if nowtime.minute == 1:
         flag = self.db.select("select * from flag_control where flag_name='moba_border_announce'")[0]["flag"]
         if flag == 1:
            await self.moba_border_get()

      nowtime = datetime.datetime.now()  # 予約投稿用にもう一度時刻取得
      await self.reservation_message_check(nowtime)

   # botがオンラインになるまでタスクを待機させる
   @time_process.before_loop
   async def bot_preparation(self):
      print('waiting...')
      await self.bot.wait_until_ready()
      req = requests.get("https://starlight.kirara.ca/api/v1/list/card_t").json()  # デレステデータベース
      with open("json/idol_data.json", "w")as f:
         json.dump(req, f, indent=3)
      req = requests.get("https://api.pink-check.school/v2/cards").json()  # モバマスデータベース
      with open("json/idol_data_moba.json", "w")as f:
         json.dump(req, f, indent=3)
      print('データベースを更新しました')
      self.weather_get()
      self.bot_status_changer.start()


def setup(bot):
   bot.add_cog(Time(bot))
