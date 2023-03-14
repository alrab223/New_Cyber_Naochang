import os

import cv2
import requests
from PIL import Image


def nhk():
   im1 = Image.open('picture/image_processing/image.png')
   im2 = Image.open('picture/image_processing//nhk.png')
   img_resize = im2.resize((int(im1.size[0] / 3.7), int(im1.size[1] / 3)))
   print(im1.size)
   print(img_resize.size)
   im1.paste(img_resize, (int(img_resize.size[0] * 2.8), int(img_resize.size[1] * 2)), img_resize)
   im1.save('picture/image_processing/new.png', quality=95)


def out():
   im1 = Image.open('picture/image_processing/image.png')
   im2 = Image.open('picture/image_processing/all_out.png')
   img_resize = im2.resize((int(im1.size[0] / 2), int(im1.size[1] / 2)))
   print(im1.size)
   print(img_resize.size)
   im1.paste(img_resize, (int(img_resize.size[0] / 2), int(img_resize.size[1])), img_resize)
   im1.save('picture/image_processing/new.png', quality=95)


def gaming():
   img1 = cv2.imread('picture/image_processing/image.png')
   img2 = cv2.imread('picture/image_processing/rainbow.jpg')
   img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2RGB)
   img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)
   img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
   blended = cv2.addWeighted(src1=img1, alpha=0.6, src2=img2, beta=0.4, gamma=0)
   cv2.imwrite('picture/image_processing/new.png', cv2.cvtColor(blended, cv2.COLOR_RGB2BGR))


def onesin():
   im1 = Image.open('picture/image_processing/image.png').convert("RGBA")
   im2 = Image.open('picture/image_processing/onesin.png').convert("RGBA")
   img_resize = im2.resize(im1.size)
   print(im2.size)
   im1.paste(img_resize, (0, 0), img_resize)
   im1.save('picture/image_processing/new.png', quality=95)


# removebgで切り抜く
def bg_remove():
   response = requests.post(
       'https://api.remove.bg/v1.0/removebg',
       files={'image_file': open('picture/image_processing/image.png', 'rb')},
       data={'size': 'auto'},
       headers={'X-Api-Key': os.environ.get("removebg_api")},
   )
   if response.status_code == requests.codes.ok:
      with open('picture/image_processing/new.png', 'wb') as out:
         out.write(response.content)
   else:
      print("Error:", response.status_code, response.text)


# ハンドラー
handler = {
    "nhk": nhk,
    "out": out,
    "ゲーミング": gaming,
    "onesin": onesin,
    "切り抜き": bg_remove
}


def image_processing(text):
   try:
      func = handler[text]
      func()
      return True
   except KeyError:
      print("キーが存在しません")
      return False
