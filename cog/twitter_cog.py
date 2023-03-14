import asyncio

from discord.ext import commands
from discord.commands import SlashCommandGroup

from cog.util.DbModule import DbModule as db
from cog.util.tweet_stream import Listener, StreamMaker
from cog.util import thread_webhook as webhook


class Twitter(commands.Cog):

   def __init__(self, bot):
      self.bot = bot
      self.stone = False
      self.stream = None
      self.stream_maker = StreamMaker()
      self.db = db()
      self.media_switch = False

   twitter_command = SlashCommandGroup('twitter_command', 'Twitter関連のコマンド')

   @commands.Cog.listener()
   async def on_ready(self):
      print('接続待機中...')
      await self.bot.wait_until_ready()
      print('-----')
      print('接続完了')
      if self.db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"] == 1:
         self.db.update("delete from Twitter_log")
         self.stream = self.stream_maker.stream_start()
         self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "tweet_get"})
         channel_id = self.db.select("select *from channel_flag_control where flag_name='tweet_get'")[0]["channel_id"]
         channel = self.bot.get_channel(channel_id)
         await self.tweet_send(channel)

   async def tweet_send(self, channel):
      while self.db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"] == 1:
         try:
            tweet = self.db.select("select *from Twitter_log limit 1")[0]
            self.db.auto_delete("Twitter_log", {"tweet_id": tweet["tweet_id"]})
         except IndexError:
            await asyncio.sleep(2)
            continue
         if self.media_switch is True and tweet["media1"] is None:
            pass
         else:
            urls = []
            medias = ["media1", "media2", "media3", "media4"]
            add_text = ""
            for media in medias:
               if tweet[media] is not None:
                  urls.append(tweet[media])
                  if "mp4" in tweet[media]:
                     add_text = "(動画があります。URL先で確認してください)"
               else:
                  break

            payload = webhook.payload_edit(tweet["user"], tweet["icon"], tweet["text"], urls)
            url = f"https://twitter.com/{tweet['screen_id']}/status/{tweet['tweet_id']}"
            payload["embeds"].append({"title": f"ツイート先に飛ぶ{add_text}", "url": url})
            Ch_webhook = await webhook.get_webhook(channel)
            webhook.custom_send(payload, Ch_webhook.url, channel)
            await asyncio.sleep(2)

   @commands.has_role("スタッフ")
   @twitter_command.command(name="ツイート取得開始")
   async def tweet_get_start(self, ctx):
      """ツイートの取得を開始します"""
      if self.db.select("select *from flag_control where flag_name='tweet_get'")[0]["flag"] == 1:
         await ctx.respond("すでにこの機能が使用されているため、現在使えません")
         return
      self.db.update("delete from Twitter_log")
      self.stream = self.stream_maker.stream_start()
      self.db.allinsert("channel_flag_control", [None, ctx.channel.id, "tweet_get"])
      self.db.auto_update("flag_control", {"flag": 1}, {"flag_name": "tweet_get"})
      await ctx.respond("ツイート取得を開始します")
      await self.tweet_send(ctx.channel)

   @commands.has_role("スタッフ")
   @twitter_command.command(name="ツイッター監視ワード追加")
   async def tweet_add_word(self, ctx, word: str):
      """監視ツイートの用語を入力してください"""
      self.db.allinsert("monitor_target", [None, word, "word"])
      if self.stream is not None:
         self.stream = self.stream_maker.add_rules(self.stream)
         await ctx.respond("ワードを追加しました。ストリームを再起動しています")
      else:
         await ctx.respond(f"{word}を監視対象に追加しました。")

   @commands.has_role("スタッフ")
   @twitter_command.command(name="ツイッター監視ユーザー追加")
   async def twitter_add_user(self, ctx, user_id: str):
      """監視ユーザーを追加します。監視対象のTwitter IDを入力してください"""
      self.db.allinsert("monitor_target", [None, user_id, "user"])

      if self.stream is not None:
         await ctx.respond("ユーザーを追加しました。ストリームを再起動しています")
         self.stream_maker.add_rules(self.stream)
      else:
         await ctx.respond(f"{user_id}を監視対象に追加しました。")

   @commands.has_role("スタッフ")
   @twitter_command.command(name="ツイッター監視ワード削除")
   async def twitter_word_monitor_delete(self, ctx, target: str):
      """監視ユーザーを削除します"""
      self.db.auto_delete("monitor_target", {"word": target})
      if self.stream is not None:
         await ctx.respond("監視対象を削除しました。ストリームを再起動しています")
         self.stream = self.stream_maker.add_rules(self.stream)
      else:
         await ctx.respond("対象を削除しました")

   @commands.has_role("スタッフ")
   @twitter_command.command(name="ツイッター監視ユーザー削除")
   async def twitter_user_monitor_delete(self, ctx, target: str):
      """監視ユーザーを削除します"""
      self.db.auto_delete("monitor_target", {"word": target})
      if self.stream is not None:
         await ctx.respond("監視対象を削除しました。ストリームを再起動しています")
         self.stream = self.stream_maker.add_rules(self.stream)
      else:
         await ctx.respond("対象を削除しました")

   @commands.has_role("スタッフ")
   @twitter_command.command(name="メディアスイッチ")
   async def media_switch(self, ctx):
      """メディア付きツイートのみ取得する"""
      if self.media_switch is False:
         self.media_switch = True
         await ctx.respond("メディア付きツイートのみを流します")
      else:
         self.media_switch = False
         await ctx.respond("全てのツイートを流します")

   @twitter_command.command(name="ツイッター監視対象一覧")
   async def twitter_user_monitor_search(self, ctx):
      """監視ワード、ユーザーIDを確認します"""
      word = self.db.select("select * from monitor_target")
      user = [x["word"] for x in word if x["type"] == "user"]
      text = [x["word"] for x in word if x["type"] == "word"]
      user = " ".join(user)
      user = f"```{user}```"
      await ctx.respond(f"監視ユーザーID\n{user}")
      text = " ".join(text)
      text = f"```{text}```"
      await ctx.send(f"監視ワード\n{text}")

   @twitter_command.command(name="ツイート取得停止")
   async def tweet_get_stop(self, ctx):
      """ツイート取得を停止します"""
      self.db.auto_update("flag_control", {"flag": 0}, {"flag_name": "tweet_get"})
      self.db.auto_delete("channel_flag_control", {"flag_name": "tweet_get"})
      self.stream.disconnect()
      await ctx.respond("ツイート取得を停止しました")

   @commands.Cog.listener()
   async def on_application_command_error(self, ctx, error):
      if isinstance(error, (commands.MissingRole, commands.MissingAnyRole, commands.CheckFailure)):
         await ctx.send("権限がありません")
      else:
         print(error)


def setup(bot):
   bot.add_cog(Twitter(bot))
