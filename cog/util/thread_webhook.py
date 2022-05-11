import discord
import requests


async def get_webhook(ctx):
   if str(ctx.channel.type) == "public_thread":
      channel = ctx.channel.parent
   else:
      channel = ctx.channel
   ch_webhooks = await channel.webhooks()
   webhook = discord.utils.get(ch_webhooks, name="naochang")
   if webhook is None:
      await channel.create_webhook(name="naochang")
      ch_webhooks = await channel.webhooks()
      webhook = discord.utils.get(ch_webhooks, name="naochang")
   return webhook


def payload_edit(username: str, avatar_url: str, content: str, attachment: list = None):
   payload = {}
   payload["username"] = username
   payload["avatar_url"] = avatar_url
   payload["content"] = content
   payload["embeds"] = []
   if attachment is None or attachment == []:
      pass
   else:
      payload["embeds"].append({"url": "https://www.pixiv.net/fanbox", "author": {"url": "https://www.pixiv.net/fanbox"}, "image": {"url": attachment.pop(0)}})
      for url in attachment:
         payload["embeds"].append({"url": "https://www.pixiv.net/fanbox", "image": {"url": url}})
   return payload


async def send(content: str, ctx, file=None):
   ch_webhooks = await get_webhook(ctx)
   if file is None:
      if str(ctx.channel.type) == "public_thread":
         await ch_webhooks.send(content=content,
                                username=ctx.author.display_name,
                                avatar_url=ctx.message.author.avatar.url,
                                thread=ctx.channel)
      else:
         await ch_webhooks.send(content=content,
                                username=ctx.author.display_name,
                                avatar_url=ctx.message.author.avatar.url)
   else:
      if str(ctx.channel.type) == "public_thread":
         await ch_webhooks.send(file=file,
                                username=ctx.author.display_name,
                                avatar_url=ctx.message.author.avatar.url,
                                thread=ctx.channel)
      else:
         await ch_webhooks.send(file=file,
                                username=ctx.author.display_name,
                                avatar_url=ctx.message.author.avatar.url)


def custom_send(payload: dict, url, ctx):
   if str(ctx.channel.type) == "public_thread":
      WEBHOOK_URL = f"{url}?thread_id={ctx.channel.id}&wait=True"
   else:
      WEBHOOK_URL = url
   payload = payload
   res = requests.post(WEBHOOK_URL, json=payload)
   return res.status_code
