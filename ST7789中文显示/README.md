# microPython驱动tft屏幕显示中文终极解决方案

## 一、运行效果

![](https://github.com/LC044/MCU/blob/main/ST7789%E4%B8%AD%E6%96%87%E6%98%BE%E7%A4%BA/picture/lv_0_20220730145237%2000_00_00-00_00_30~1.gif)

## 二、实现原理

原理同上篇文章一样，用在线汉字取模工具获取点阵的字节信息，通过st7789py.py驱动程序显示出来。

上次的程序只能显示部分汉字，需要显示哪些字自己去在线网站取模，然后存到程序里。不过像我这么懒的人，怎么可能一个一个取模啊。

我粗略一算gb2312不到8000个字符，对于16x16大小的汉字，每个汉字需要16*16bit，也就是32个字节，8000个字也就250k，这对于有4M flash的esp32简直绰绰有余啊。

想到是在浏览器上取模，浏览器能干的活python都能干，于是我写了一个爬虫程序，把七千多个汉字的点阵数据爬了下来。

[汉字取模网址](https://www.zhetao.com/fontarray.html)：https://www.zhetao.com/fontarray.html

爬虫代码：

```python
import struct
from selenium import webdriver
from selenium.webdriver.common.by import By


class lattice(object):
    def __init__(self, size):
        # size 为字体的大小
        options = webdriver.ChromeOptions()
        options.add_argument('User-Agent=Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)')
        '''
        这里写Chrome浏览器地址和Chromedriver地址
        一般不用，可以删去
        我把chrome.exe改名了系统找不到，所以加上了地址
        '''
        options.binary_location = r'D:\Program Files\Google\Chrome\Application\chrom.exe'
        self.browser = webdriver.Chrome('D:\Program Files\Google\Chrome\Application\chromedriver.exe', options=options)

        self.url = 'https://www.zhetao.com/fontarray.html'
        self.size = size // 8

    def set_size(self):
        width = self.browser.find_element(by=By.XPATH, value='/html/body/div[1]/div[1]/input[1]')
        height = self.browser.find_element(by=By.XPATH, value='/html/body/div[1]/div[1]/input[2]')
        width.click()
        width.clear()
        width.send_keys(str(self.size))
        height.click()
        height.clear()
        height.send_keys(str(self.size * 8))

    def get_bytes(self, font):
        self.ele_font.clear()
        self.ele_font.send_keys(font)
        self.browser.find_element(by=By.XPATH, value='/html/body/div[1]/div[1]/input[7]').click()
        result = self.browser.find_element(by=By.XPATH, value='/html/body/div[1]/div[4]/div')
        bytes = result.text.split('{')[self.size + 1].split('}')[0].splitlines()
        r = b''
        t = ''
        for b in bytes:
            if len(b) > 1:
                b = b.strip(' ').split(',')
                for k in b:
                    if k:
                        # print(k.strip(' '))
                        r += int(k.strip(' ')[2:4], 16).to_bytes(1, 'big')
                        t += k.strip(' ')
        return r, t

    def b2i(self, byte):
        r = 0
        for i in range(len(byte)):
            r = (r << 8) + byte[i]
        return r

    def i2b(self, num):
        # num = int(num, 16)
        return num.to_bytes(3, 'big')

    def run(self):
        self.browser.get(self.url)
        self.ele_font = self.browser.find_element(by=By.XPATH,
                                                  value='/html/body/div[1]/div[1]/input[6]')
        self.set_size()
        font = []
        for i in range(0, 65535):
            hi_byte = i >> 8
            lo_byte = i & 0xff
            hz = struct.pack('<BB', hi_byte, lo_byte)
            # print(hz)
            # break

            try:
                hz: str = hz.decode(encoding='gb2312')  # 按GB2312解码
                if len(hz) == 1:
                    code_gb2312 = hz.encode(encoding='gb2312')
                    print(code_gb2312, '0x%04x' % (code_gb2312[0] * 256 + code_gb2312[1]), end=', ')
                    code_unicode = hz.encode(encoding='utf-8')
                    print('0x' + str(code_unicode)[:-1], end=', ')
                    print('// ' + hz, (self.b2i(code_gb2312) - 41448 + 67) * 128)
                    if self.b2i(code_unicode) > 14844052:
                        try:
                            bytes, txt = self.get_bytes(code_unicode.decode('utf-8'))
                            font.append((self.b2i(code_unicode), bytes))
                        except:
                            print('error')
                    # time.sleep(0.5)
            except:
                pass
        # 按编码排序，以便使用二分查找
        font.sort(key=lambda x: x[0])
        t = open(f'gb{self.size * 8}x{self.size * 8}.ttf', 'wb')
        for f in font:
            t.write(self.i2b(f[0]))
            t.write(f[1])
        print(len(font))
        t.close()
        self.browser.close()

    def __del__(self):
        pass


if __name__ == '__main__':
    # 括号里填写字体大小
    # 必须为8的倍数，如16,24,32
    l = lattice(16)
    l.run()

```

数据爬下来了，但是应该怎样存储呢，microPython里只支持utf-8编码，而utf-8和gbk编码里汉字的储存码是不连续的，用散列表映射会有很多浪费空间，我试了一下，原本只有250k的数据，用gbk编码散列映射需要691k，用utf-8映射可能需要再翻很多倍，散列表映射虽然查找比较快，但是很费空间。

于是，我选择用时间换空间，把汉字数据按utf-8编码排序，顺序储存，最后采用二分法查找汉字的点阵数据。

.ttf文件数据存储格式 utf-8码+点阵数据，所以对于每个汉字，所需要的数据在原来点阵数据的基础上又加了3个字节的utf-8编码

例如：16x16大小的'周'

```python
'\xe5\x91\xa8'   "\x00\x00?\xf8!\x08!\x08/\xe8!\x08!\x08?\xf8 \x08'\xc8$H$H'\xc8@\x08@(\x80\x10"
```

## 三、字体

数据储存完了，接下来就是查找

代码如下（**数据存在esp32的package文件夹里**）：

```python
class Font:
    def __init__(self,size):
        self.WIDTH = size
        self.HEIGHT = size
        self.SIZE = size * (size // 8)
        self.FONT = {}
    
class gb2312(object):
    def __init__(self,size):
        self.f = open('./package/gb{0}x{0}.ttf'.format(size), 'rb')
        self.height = size
        self.size = size * (size // 8) + 3
    def b2i(self, byte):
        r = 0
        for i in range(len(byte)):
            r = (r << 8) + byte[i]
        return r

    def i2b(self, num):
        return num.to_bytes(3, 'big')

    def one_char(self, char):
        utf_byte = char.encode('utf-8')
        return self.B_S(0, 7296, self.b2i(utf_byte))
    
    def str(self,st):
        font = Font(self.height)
        for s in st:
            data = self.one_char(s) 
            font.FONT[s] = data if data else self.one_char('一')
        return font
    def B_S(self, low, high, m):
        if low >= 0 and high <= 7296 and low <= high:
            mid = (low + high) // 2
            self.f.seek(mid * self.size)
            data = self.f.read(self.size)
            utf = self.b2i(data[0:3])
            if utf < m:
                return self.B_S(mid + 1, high, m)
            elif utf > m:
                return self.B_S(low, mid - 1, m)
            else:
                return data[3:]
    def __del__(self):
        self.f.close()

if __name__ == '__main__':
    F = gb2312(24)
    char = F.one_char('周')
    t = F.str('你好！世界')
    print(t.HEIGHT,t.FONT)
```

那么我想自定义其他字号的字体怎么办？

终极解决办法

```python
class Font:
    def __init__(self, size):
        self.WIDTH = size
        self.HEIGHT = size
        self.SIZE = size * (size // 8)


class Font32(Font):
    def __init__(self,size):
        Font.__init__(self,size)
        '''
        想要哪个汉字，自己往后加
        '''
        self.FONT = {
        '℃': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f,
              0x80, 0x00, 0x00, 0x1f, 0xc3, 0xff, 0x00, 0x1d, 0xc7, 0xff, 0xb0, 0x1d, 0xcf, 0x83, 0xf0, 0x1d, 0xde,
              0x00, 0xf0, 0x1f, 0xfc, 0x00, 0x70, 0x07, 0x3c, 0x00, 0x70, 0x00, 0x78, 0x00, 0x30, 0x00, 0x78, 0x00,
              0x30, 0x00, 0x78, 0x00, 0x30, 0x00, 0x78, 0x00, 0x00, 0x00, 0x78, 0x00, 0x00, 0x00, 0x78, 0x00, 0x00,
              0x00, 0x78, 0x00, 0x00, 0x00, 0x78, 0x00, 0x00, 0x00, 0x78, 0x00, 0x00, 0x00, 0x78, 0x00, 0x00, 0x00,
              0x3c, 0x00, 0x00, 0x00, 0x3c, 0x00, 0x30, 0x00, 0x3e, 0x00, 0x70, 0x00, 0x1f, 0x01, 0xe0, 0x00, 0x0f,
              0x87, 0xc0, 0x00, 0x07, 0xff, 0x80, 0x00, 0x03, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        '晴': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1c, 0x00, 0x00, 0x00, 0x1e, 0x30, 0x00,
              0x00, 0x1c, 0x78, 0x38, 0xff, 0xff, 0xfc, 0x3f, 0xfc, 0x1c, 0x00, 0x38, 0xf0, 0x1c, 0x00, 0x38, 0xe0,
              0x1c, 0xf0, 0x38, 0xe7, 0xff, 0xf8, 0x38, 0xe3, 0x1c, 0x00, 0x38, 0xe0, 0x1c, 0x18, 0x38, 0xe0, 0x1c,
              0x3c, 0x38, 0xff, 0xff, 0xfe, 0x3f, 0xfc, 0x00, 0x00, 0x38, 0xe7, 0x00, 0xf0, 0x38, 0xe3, 0xff, 0xf0,
              0x38, 0xe3, 0x80, 0xf0, 0x38, 0xe3, 0x80, 0xe0, 0x38, 0xe3, 0xff, 0xe0, 0x38, 0xe3, 0x80, 0xe0, 0x38,
              0xe3, 0x80, 0xe0, 0x3f, 0xe3, 0x80, 0xe0, 0x38, 0xe3, 0xff, 0xe0, 0x38, 0xe3, 0x80, 0xe0, 0x38, 0xe3,
              0x80, 0xe0, 0x30, 0x03, 0x80, 0xe0, 0x00, 0x03, 0x80, 0xe0, 0x00, 0x03, 0x8f, 0xe0, 0x00, 0x03, 0x87,
              0xe0, 0x00, 0x07, 0x01, 0xe0, 0x00, 0x00, 0x00, 0x00],
        '雨': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x38, 0x00,
              0x00, 0x00, 0x78, 0x3f, 0xff, 0xff, 0xfc, 0x1c, 0x03, 0x80, 0x00, 0x00, 0x03, 0x80, 0x00, 0x00, 0x03,
              0x80, 0x00, 0x0e, 0x03, 0x80, 0xf0, 0x0f, 0xff, 0xff, 0xf8, 0x0e, 0x03, 0x80, 0xf0, 0x0f, 0xc3, 0xa0,
              0xf0, 0x0f, 0xf3, 0xf8, 0xf0, 0x0e, 0xfb, 0xbe, 0xf0, 0x0e, 0x7f, 0x9e, 0xf0, 0x0e, 0x3f, 0x8e, 0xf0,
              0x0e, 0x3b, 0x8e, 0xf0, 0x0e, 0x1b, 0x86, 0xf0, 0x0f, 0x83, 0x80, 0xf0, 0x0f, 0xe3, 0xf8, 0xf0, 0x0e,
              0xfb, 0xbe, 0xf0, 0x0e, 0x7b, 0x9e, 0xf0, 0x0e, 0x3b, 0x8f, 0xf0, 0x0e, 0x3b, 0x8f, 0xf0, 0x0e, 0x1b,
              0x86, 0xf0, 0x0e, 0x03, 0x80, 0xf0, 0x0e, 0x03, 0x9f, 0xf0, 0x0e, 0x03, 0x9f, 0xe0, 0x0e, 0x03, 0x83,
              0xe0, 0x0e, 0x03, 0x01, 0xc0, 0x00, 0x00, 0x00, 0x00],
        '雾': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x80, 0x03, 0xff, 0xff, 0xc0, 0x01,
              0xc3, 0xc0, 0x00, 0x06, 0x03, 0xc0, 0x38, 0x0f, 0xff, 0xff, 0xfc, 0x0e, 0x03, 0xc0, 0x7c, 0x1f, 0xff,
              0xff, 0xf0, 0x3e, 0x03, 0xc0, 0xe0, 0x19, 0xff, 0xff, 0x80, 0x00, 0x03, 0xc0, 0x00, 0x00, 0x3b, 0x80,
              0x00, 0x00, 0x7c, 0x0f, 0x00, 0x00, 0xff, 0xff, 0x80, 0x01, 0xf8, 0x1f, 0x80, 0x03, 0xdc, 0x3c, 0x00,
              0x0f, 0x0f, 0xf0, 0x00, 0x0e, 0x07, 0xf0, 0x00, 0x00, 0x3f, 0xff, 0xfe, 0x01, 0xff, 0x3f, 0xfe, 0x1f,
              0xe7, 0x87, 0xf8, 0x7c, 0x07, 0x83, 0x80, 0x03, 0xff, 0xff, 0xc0, 0x01, 0xcf, 0x03, 0x80, 0x00, 0x0f,
              0x07, 0x80, 0x00, 0x1e, 0x07, 0x00, 0x00, 0x3c, 0x07, 0x00, 0x00, 0xf8, 0xff, 0x00, 0x07, 0xe0, 0x7e,
              0x00, 0x3f, 0x00, 0x3e, 0x00, 0x00, 0x00, 0x00, 0x00],
        '': [],
        '': [],
    }
class Font48(Font):
    def __init__(self,size):
        Font.__init__(self,size)
        '''
        这个是显示的半角英文字符，所以字体宽度和size都需要单独设置
        '''
        self.WIDTH = 24
        self.SIZE = 144
        self.FONT = {
            '1': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x00, 0x1c, 0x00, 0x00, 0xfc, 0x00, 0x07,
                  0xfc, 0x00, 0x07, 0xfc, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00,
                  0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c,
                  0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00,
                  0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00,
                  0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00, 0x00, 0x3e, 0x00, 0x00, 0x7e, 0x00, 0x07, 0xff,
                  0xf0, 0x07, 0xff, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
            '2': [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0xff, 0x80, 0x07, 0xff, 0xe0, 0x0f, 0x83, 0xf0, 0x1f,
                  0x01, 0xf0, 0x1e, 0x00, 0xf8, 0x1e, 0x00, 0xf8, 0x3e, 0x00, 0xf8, 0x3f, 0x00, 0x78, 0x3f, 0x00, 0x78,
                  0x3f, 0x00, 0x78, 0x1f, 0x00, 0xf8, 0x00, 0x00, 0xf8, 0x00, 0x00, 0xf8, 0x00, 0x01, 0xf0, 0x00, 0x03,
                  0xf0, 0x00, 0x03, 0xe0, 0x00, 0x07, 0xc0, 0x00, 0x0f, 0x80, 0x00, 0x1f, 0x00, 0x00, 0x3e, 0x00, 0x00,
                  0x7c, 0x00, 0x00, 0xf8, 0x00, 0x01, 0xf0, 0x00, 0x03, 0xe0, 0x00, 0x03, 0xc0, 0x00, 0x07, 0x80, 0x1c,
                  0x0f, 0x00, 0x1c, 0x1f, 0x00, 0x38, 0x3e, 0x00, 0x38, 0x3c, 0x00, 0xf8, 0x3f, 0xff, 0xf8, 0x3f, 0xff,
                  0xf8, 0x3f, 0xff, 0xf8, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00],
        }
if __name__ == '__main__':
    f32 = Font32(32)
    f48 = Font48(48)
    print(f32.SIZE)
    print(f48.WIDTH)
```
## 四、st7789py.py驱动修改

1. 模块导入

   ```python
   '''
   导入字体
   '''
   from package import GBfont
   from package import vga1_16x32 as font
   from package import font_gb_16x16 as font_gb
   GB16 = GBfont.gb2312(16)
   GB24 = GBfont.gb2312(24)
   GB32 = font_gb.Font32(32)
   GB48 = font_gb.Font48(48
   ```

2. text_gb显示中文

   ```python
   def text_gb(self,font,size, text, x0, y0, color=WHITE, background=BLACK):
       """
       显示中文
       font (class): 字体
       size (int): 字体大小
       text (str): 要显示的中文文本（不能含有半角英文符号）
       x0 (int): column to start drawing at
       y0 (int): row to start drawing at
       color (int): 565 encoded color to use for background
       background (int): 565 encoded color to use for background
       """
       for char in text:
           if (x0+font.WIDTH <= self.width and y0+font.HEIGHT <= self.height):
               for line in range(2):  # 分两次显示，先显示上半边后显示下半边
                       idx = line * (font.SIZE//2)
                       buffer = b''
                       for x in range((font.SIZE//2)):
                           for i in range(8):
                               buffer += struct.pack('H',color if font.FONT[char][idx+x] & _BIT[7-i] else background)
                       self.blit_buffer(buffer, x0, y0+(font.HEIGHT//2)*line, font.WIDTH, font.HEIGHT//2)
               x0 += font.WIDTH  # 显示下一个字的时候x坐标增加字体宽度
   ```

   

3. 修改text方法

   ```python
   def text(self,size, text, x0, y0, color=WHITE, background=BLACK):
       """
       Draw text on display in specified font and colors. 8 and 16 bit wide
       fonts are supported.
       Args:
           font (module): font module to use.
           text (str): text to write
           x0 (int): column to start drawing at
           y0 (int): row to start drawing at
           color (int): 565 encoded color to use for characters
           background (int): 565 encoded color to use for background
       """
       char = text[0].encode('utf-8')
       if len(char) == 1 and size <= 32:
           if font.WIDTH == 8:
               self._text8(font, text, x0, y0, color, background)
           else:
               self._text16(font, text, x0, y0, color, background)
       else:
           if size == 16:
               font_gb = GB16.str(text)
           elif size == 24:
               font_gb = GB24.str(text)
           elif size == 32:
               font_gb = GB32
           elif size == 48:
               font_gb = GB48
           self.text_gb(font_gb,size, text, x0, y0, color, background)
   ```

   
## 五、测试代码

```python
from machine import Pin, SPI
from package import st7789py as st
import time


class Display():
    def __init__(self):
        self.tft = st.ST7789(SPI(2, 10000000), 240, 240, reset=Pin(17), dc=Pin(2), cs=Pin(5), backlight=Pin(22), rotation=0)
        self.WHITE = st.color565(255, 255, 255)#BRG
        self.BLACK = st.color565(0, 0, 0)
        self.RED = st.color565(0, 0, 255)
        self.last_hour = 0
        self.last_minute = 0
        self.last_second = 0
        self.last_year = 0
        self.last_month = 0
        self.last_day = 0
        self.clock_x = 20+24*2-12
        self.clock_y = 90
        self.init_show()
        
    def init_show(self):
        '''
        初始化显示画面
        '''
        self.tft.fill(0)
        print('ok')
        time.sleep(2)
        """
        风急天高猿啸哀，渚清沙白鸟飞回。
        无边落木萧萧下，不尽长江滚滚来。
        万里悲秋常作客，百年多病独登台。
        艰难苦恨繁霜鬓，潦倒新停浊酒杯。
        """
        self.tft.text(24, '登高', 100, 0, self.WHITE, self.BLACK)
        self.tft.text(24, '—杜甫', 140, 30, self.WHITE, self.BLACK)
        self.tft.text(16, '风急天高猿啸哀，渚清沙白鸟飞回。', 0, 70, self.WHITE, self.BLACK)
        self.tft.text(16, '无边落木萧萧下，不尽长江滚滚来。', 0, 90, self.WHITE, self.BLACK)
        self.tft.text(16, '万里悲秋常作客，百年多病独登台。', 0, 110, self.WHITE, self.BLACK)
        self.tft.text(16, '艰难苦恨繁霜鬓，潦倒新停浊酒杯。', 0, 130, self.WHITE, self.BLACK)
        self.tft.text(24, '众鸟高飞尽孤云独去闲。', 0, 210, self.WHITE, self.BLACK)
        self.tft.text(24, '相看两不厌只有敬亭山。', 0, 170, self.WHITE, self.BLACK)
        

    def show_time(self,t):
        t = time.localtime(time.time())
        '''
        显示时间
        '''
        year = t[0]
        month = t[1]
        day = t[2]
        hour = t[3]
        minute = t[4]
        second = t[5]
        ti = "{:0>2d}:{:0>2d}:{:0>2d}".format(hour,minute,second)
        #print(ti)
        if hour != self.last_hour:
            self.tft.text(48, '{:0>2d}'.format(hour), self.clock_x, self.clock_y, self.WHITE, self.BLACK)
            self.last_hour = hour
        if minute != self.last_minute:
            self.tft.text(48, '{:0>2d}'.format(minute), self.clock_x + 24*3, self.clock_y, self.WHITE, self.BLACK)
            self.last_minute = minute
        
        
    def run(self):
        pass
            
        
    def __del__(self):
        pass
D = Display()
D.run()
```

运行结果见开头

# 六、附件下载

点击下载[GitHub地址](https://github.com/LC044/MCU/tree/main/ST7789%E4%B8%AD%E6%96%87%E6%98%BE%E7%A4%BA)

天气时钟

![](https://github.com/LC044/MCU/blob/main/ST7789%E4%B8%AD%E6%96%87%E6%98%BE%E7%A4%BA/picture/lv_0_20220730145250%2000_00_00-00_00_30~1.gif)
