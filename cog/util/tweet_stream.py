import json
import os
from datetime import timedelta

import tweepy
from cog.util.DbModule import DbModule as db

db = db()


class Listener(tweepy.StreamingClient):

   def on_data(self, data):
      flag = db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"]
      if flag == 0:
         self.disconnect()
         return
      data = json.loads(data.decode())
      try:
         user = data["includes"]["users"][0]["name"]
         text = data["data"]["text"]
         icon = data["includes"]["users"][0]["profile_image_url"]
         screen_id = data["includes"]["users"][0]["username"]
         tweet_id = data["data"]["id"]
      except KeyError:
         print(data)
         return

      if data["data"]["attachments"] != {}:  # URLが含まれていた場合
         try:
            for url in data["data"]["entities"]["urls"]:
               text = text.replace(url["url"], "")
         except KeyError:
            pass
      content = [tweet_id, screen_id, user, text, icon]

      if data["data"]["attachments"] != {}:
         add_media = []
         try:
            for media in data["includes"]["media"]:
               if media["type"] == "photo":
                  add_media.append(media["url"])
               else:
                  add_media.append(media["variants"][0]["url"])
         except KeyError:
            pass
         content += add_media
      loss = [None] * (9 - len(content))
      content += loss
      db.allinsert("Twitter_log", content)
      return True

   def on_connect(self):
      print("接続しました")

   def on_disconnect(self):
      print("切断しました")
      self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "tweet_get"})
      self.db.auto_delete("channel_flag_control", {"flag_name": "tweet_get"})

   def on_error(self, status_code):
      print('エラー発生: ' + str(status_code))

   def on_timeout(self):
      print('Timeout...')
      return True


class StreamMaker():

   def get_stream(self):
      BS = os.environ.get("Twitter_API_BS")
      stream = Listener(BS)
      return stream

   def delete_rules(self, stream):
      prev_id = stream.get_rules().data
      if prev_id is None:
         return stream
      for id in prev_id:
         stream.delete_rules(id.id)
      return stream

   def add_rules(self, stream):
      stream = self.delete_rules(stream)
      target = db.select("select * from monitor_target")
      t_list = []
      for i in target:
         if i["type"] == "user":
            t_list.append(f"from:{i['word']}")
         else:
            t_list.append(i['word'])
      target = " OR ".join(t_list)
      print(target)
      rules = f"({target}) -is:retweet -is:reply"
      stream.add_rules(tweepy.StreamRule(rules))
      return stream

   def stream_start(self):
      stream = self.get_stream()
      stream = self.add_rules(stream)
      media = ["preview_image_url", "url", "variants"]
      field = ["attachments", "author_id", "entities"]
      user = ['profile_image_url']
      expansions = ["author_id", "attachments.media_keys"]
      stream.filter(media_fields=media, expansions=expansions, tweet_fields=field, user_fields=user, threaded=True)
      return stream


if __name__ == "__main__":
   StreamMaker().word_stream()
