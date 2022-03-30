import glob
import os

import cv2
import numpy
import requests
from cog.util import file_download as pd
from PIL import Image


class PicCtx:
   def mirikora2(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla/コラ.png')
      img_resize = im2.resize(im1.size)
      print(im2.size)
      im1.paste(img_resize, (0, 0), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def ppp(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla/PPP.png')
      img_resize = im2.resize(im1.size)
      print(im2.size)
      im1.paste(img_resize, (0, 0), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def deresute_kora(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla/デレステコラ.png')
      img_resize = im2.resize(im1.size)
      print(im2.size)
      im1.paste(img_resize, (0, 0), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def nhk(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla//nhk.png')
      img_resize = im2.resize((int(im1.size[0] / 3.7), int(im1.size[1] / 3)))
      print(im1.size)
      print(img_resize.size)
      im1.paste(img_resize, (int(img_resize.size[0] * 2.8), int(img_resize.size[1] * 2)), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def bazirisuku(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla//baji.png')
      img_resize = im2.resize((int(im1.size[0] / 1.5), int(im1.size[1] / 1.4)))
      print(im1.size)
      print(img_resize.size)
      im1.paste(img_resize, (int(img_resize.size[0] / 3.4), int(img_resize.size[1] / 3)), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def out(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla/all_out.png')
      img_resize = im2.resize((int(im1.size[0] / 2), int(im1.size[1] / 2)))
      print(im1.size)
      print(img_resize.size)
      im1.paste(img_resize, (int(img_resize.size[0] / 2), int(img_resize.size[1])), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def friend_train(self):
      im1 = Image.open('picture/colla/image.png')
      im2 = Image.open('picture/colla/friend_train.png')
      img_resize = im2.resize((int(im1.size[0]), int(im1.size[1] // 2)))
      print(im1.size)
      print(img_resize.size)
      im1.paste(img_resize, (0, int(im1.size[1] // 2)), img_resize)
      im1.save('picture/colla/new.png', quality=95)

   def tanuki_dance(self):
      files = sorted(glob.glob('picture/colla/tanuki/*.png'))
      images = []
      for name in files:
         im2 = Image.open('picture/colla/image.png').convert("RGBA")
         img = Image.open(name).convert("RGBA")
         img_resize = img.resize((int(im2.size[0]), int(im2.size[1] / 3)))
         im2.paste(img_resize, (0, int(im2.size[1] - im2.size[1] / 3)), img_resize)
         images.append(im2)
      images[0].save('picture/colla/tanuki/image.gif', save_all=True,
                     disposal=2, append_images=images[1:], duration=100, loop=0)

   def bg_remove(self):
      response = requests.post(
          'https://api.remove.bg/v1.0/removebg',
          files={'image_file': open('picture/colla/image.png', 'rb')},
          data={'size': 'auto'},
          headers={'X-Api-Key': os.getenv('remove_bg_API')},
      )
      if response.status_code == requests.codes.ok:
         with open('picture/colla/no-bg.png', 'wb') as out:
            out.write(response.content)
      else:
         print("Error:", response.status_code, response.text)

   def gray_scale(self):
      gamma22LUT = numpy.array([pow(x / 255.0, 2.2) for x in range(256)], dtype='float32')
      img_bgr = cv2.imread('picture/colla/image.jpg')
      img_bgrL = cv2.LUT(img_bgr, gamma22LUT)
      img_grayL = cv2.cvtColor(img_bgrL, cv2.COLOR_BGR2GRAY)
      img_gray = pow(img_grayL, 1.0 / 2.2) * 255
      cv2.imwrite('picture/colla/new.jpg', img_gray)

   def main(self, message, time_wait: bool):
      pd.download_img(message.attachments[0].url, "picture/colla/image.png")
      if message.content == "ミリシタコラ":
         self.mirikora2()
         return 1
      elif message.content == "バジリスク":
         self.bazirisuku()
         return 1
      elif message.content == "デレステコラ":
         self.deresute_kora()
         return 1
      elif message.content == "優しい世界観":
         self.ppp()
         return 1
      elif message.content == "全員アウト":
         self.out()
         return 1
      elif message.content == "友情トレーニング":
         self.friend_train()
         return 1
      elif message.content == "切り抜き":
         self.bg_remove()
         return 2
      elif message.content == 'グレースケール':
         pd.download_img(message.attachments[0].url, "picture/colla/image.jpg")
         self.gray_scale()
         return 5
      elif message.content == "たぬきダンス":
         pd.download_img(message.attachments[0].url, "picture/colla/image.jpg")
         self.tanuki_dance()
         return 6
      elif message.content == "デレマス解析":
         pd.download_img(message.attachments[0].url, "yolov5/data/images/image.png")
         return 7
