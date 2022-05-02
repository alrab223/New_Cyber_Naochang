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
      if flag == 0:  # コマンドで0になったら切断
         self.disconnect()
         return
      status.created_at += timedelta(hours=9)
      user = status.author.name  # ユーザー名
      text = status.text.replace(words, "")  # ツイート
      icon = status.author.profile_image_url.replace("normal", "400x400")  # アイコン
      screen_id = status.user.screen_name
      tweet_id = status.id
      content = [tweet_id, screen_id, user, text, icon]

      if "retweeted_status" in status._json.keys():
         return True
      if hasattr(status, 'extended_entities'):  # メディアの確認
         ex_media = status.extended_entities['media']
         image_url = []
         if 'video_info' in ex_media[0]:
            ex_media_video_variants = ex_media[0]['video_info']['variants']
            if 'animated_gif' == ex_media[0]['type']:  # GIFファイルの時
               gif_url = (ex_media_video_variants[0]['url'])
               content[2] += "\n" + gif_url
            else:  # 動画ファイルの時
               bitrate_array = []
               for movie in ex_media_video_variants:
                  bitrate_array.append(movie.get('bitrate', 0))
               max_index = bitrate_array.index(max(bitrate_array))
               movie_url = ex_media_video_variants[max_index]['url']
               content[2] += "\n" + movie_url

         else:  # 画像ファイルの時
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
   word = "#" + word  # ハッシュタグ検索用
   global words
   CK = os.environ.get("Twitter_API_CK")
   CS = os.environ.get("Twitter_API_CS")
   AT = os.environ.get("Twitter_API_AT")
   AS = os.environ.get("Twitter_API_AS")
   words = word
   stream = Listener(CK, CS, AT, AS)
   stream.filter(track=[word], threaded=True)


if __name__ == "__main__":
   main()
