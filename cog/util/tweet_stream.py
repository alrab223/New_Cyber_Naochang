# twitter-stream1.py
import os
from datetime import timedelta

import tweepy
from cog.util.DbModule import DbModule as db

db = db()
words = ""


class Listener(tweepy.Stream):

   def on_status(self, status):
      flag = db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"]
      if flag == 0:
         self.disconnect()
         print("切断しました")
         return
      status.created_at += timedelta(hours=9)
      user = status.author.name
      text = status.text.replace(words, "")
      icon = status.author.profile_image_url.replace("normal", "400x400")
      screen_id = status.user.screen_name
      tweet_id = status.id
      content = [tweet_id, screen_id, user, text, icon]

      if "retweeted_status" in status._json.keys():
         return True
      # if random.randint(1, 2) != 1:#対象が多いときの対策
      #     return True
      if hasattr(status, 'extended_entities'):  # メディアファイルの確認
         ex_media = status.extended_entities['media']
         image_url = []
         if 'video_info' in ex_media[0]:
            ex_media_video_variants = ex_media[0]['video_info']['variants']
            if 'animated_gif' == ex_media[0]['type']:
               # GIFファイル
               gif_url = (ex_media_video_variants[0]['url'])
               content[2] += "\n" + gif_url
            else:
               # 動画ファイル
               bitrate_array = []
               for movie in ex_media_video_variants:
                  bitrate_array.append(movie.get('bitrate', 0))
               max_index = bitrate_array.index(max(bitrate_array))
               movie_url = ex_media_video_variants[max_index]['url']
               content[2] += "\n" + movie_url

         else:
            # 画像ファイル
            for image in ex_media:
               image_url.append(image['media_url'])
            content += image_url

      loss = [None] * (9 - len(content))
      db.allinsert("Twitter_log", content + loss)
      return True

   def on_error(self, status_code):
      print('エラー発生: ' + str(status_code))

   def on_timeout(self):
      print('Timeout...')
      return True


def main(word: str):
   global words
   CK = os.environ.get("CK")
   CS = os.environ.get("CS")
   AT = os.environ.get("AT")
   AS = os.environ.get("AS")
   words = word
   stream = Listener(CK, CS, AT, AS)
   stream.filter(track=[word], threaded=True)


if __name__ == "__main__":
   main()