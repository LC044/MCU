# ESP32使用microPython控制1.54寸240x240彩色屏幕

王铭东老师[B站视频](https://www.bilibili.com/video/BV1G34y1E7tE?p=10&vd_source=13a6ca1b8ea2bd3d76cf79603acf8ccc)详细讲解了讲了关于240x240屏幕的一些基础东西，我这里在原功能的基础上拓展了中文显示的功能，顺带修改了实际操作过程中程序中遇到的一些问题

## 一、运行效果

![](https://github.com/LC044/MCU/blob/main/ST7789/image/gif_2022_0725_211323.gif)

## 二、240x240屏幕

![](https://github.com/LC044/MCU/blob/main/ST7789/image/650273-20211217190757546-652608122.png)

ST7789有 **ST7789**, **ST7789V**, **ST7789H2**等型号, 分辨率有240x204, 240x240, 240x320等多种类型, 驱动方式都是一样的.

引脚定义：

- RES  ->  RESET复位引脚
- DC  ->  数据，指令选择引脚，1为数据 、0为指令
- CS  ->  Chip Select低电平有效
- SCK,SCL, CLK  ->  SPI串行时钟信号
- BL  ->  背光引脚，高电平点亮屏幕，低电平关闭屏幕
- SDA  ->  SPI串行数据输入输出信号
- GND  ->  电源地
- VCC  ->  支持3.3v和5v输入

## 三、硬件连接



|    ESP32    | 240x240屏幕 |
| :---------: | :---------: |
| 3V3 (or 5V) |     VCC     |
|     GND     |     GND     |
|   GPIO18    |     SCL     |
|   GPIO23    |     SDA     |
|    GPIO2    |     DC      |
|    GPIO5    |     CS      |
|   GPIO22    |     BL      |
|   GPIO17    |     RES     |

## 四、驱动下载

### 4.1、驱动下载地址

st7789py.py：https://github.com/russhughes/st7789py_mpy

### 4.2、bug修改

使用原作者驱动的时候发现屏幕不亮，对原驱动代码稍加修改能够成功显示画面

* 将204、205行代码注释掉

  ```python
  #self.hard_reset()
  #self.soft_reset()
  ```

  后面加上三行代码

  ```python
  self.cs.init(self.cs.OUT, value=1)
  self.dc.init(self.dc.OUT, value=0)
  self.reset.init(self.reset.OUT, value=1)
  ```

  

* 215、216行代码替换成

  ```python
  if backlight is not None:
      #backlight.value(1)
      self.backlight.init(self.cs.OUT, value=1)
  ```

### 4.3、支持中文显示（还不完善）

st7789类中增加三个方法

1. 显示16x16大小的中文

   ```python
       def _text_gb16(self, font,size, text, x0, y0, color=WHITE, background=BLACK):
           for char in text:
               if (x0+font.FONT['WIDTH'] <= self.width and y0+font.FONT['HEIGHT'] <= self.height):
                   for line in range(2):
                           idx = line * 16
                           buffer = b''
                           for x in range(16):
                               for i in range(8):
                                   buffer += struct.pack('H',color if font.FONT[char][idx+x] & _BIT[7-i] else background)
                           self.blit_buffer(buffer, x0, y0+8*line, 16, 8)
                   x0 += font.WIDTH
   ```

   

2. 显示24x24大小的中文

   ```python
       def text_gb24(self, font,size, text, x0, y0, color=WHITE, background=BLACK):
           for char in text:
               if (x0+font.FONT_24['WIDTH'] <= self.width and y0+font.FONT_24['HEIGHT'] <= self.height):
                   for line in range(3):#分成3次显示
                       idx = line * (font.FONT_24['SIZE']//3)
                       buffer = b''
                       for x in range(font.FONT_24['SIZE']//3):
                           for i in range(8):
                               buffer += struct.pack('H',color if font.FONT_24[char][idx+x] & _BIT[7-i] else background)
                       self.blit_buffer(buffer, x0, y0+8*line, font.FONT_24['WIDTH'], 8)
                   x0 += font.FONT_24['WIDTH']
   ```

   

3. 显示32x32大小的中文

   ```python
       def text_gb32(self, font,size, text, x0, y0, color=WHITE, background=BLACK):
           for char in text:
               if (x0+font.FONT_32['WIDTH'] <= self.width and y0+font.FONT_32['HEIGHT'] <= self.height):
                   for line in range(4):
                       idx = line * (font.FONT_32['SIZE']//4)
                       buffer = b''
                       for x in range(font.FONT_32['SIZE']//4):
                           for i in range(8):
                               buffer += struct.pack('H',color if font.FONT_32[char][idx+x] & _BIT[7-i] else background)
                       self.blit_buffer(buffer, x0, y0+8*line, font.FONT_32['WIDTH'], 8)
                   x0 += font.FONT_32['WIDTH']
   ```

   

4. 显示48x48大小的中文

   ```python
       def text_gb48(self, font,size, text, x0, y0, color=WHITE, background=BLACK):
           for char in text:
               if (x0+font.FONT_48['WIDTH'] <= self.width and y0+font.FONT_48['HEIGHT'] <= self.height):
                   for line in range(4):#分成4次显示
                       idx = line * (font.FONT_48['SIZE']//4)
                       buffer = b''
                       for x in range(font.FONT_48['SIZE']//4):
                           for i in range(8):
                               buffer += struct.pack('H',color if font.FONT_48[char][idx+x] & _BIT[7-i] else background)
                       self.blit_buffer(buffer, x0, y0+12*line, font.FONT_48['WIDTH'], 12)
                   x0 += font.FONT_48['WIDTH']
   ```

   

5. text方法修改

   ```python
       def text(self,font,size, text, x0, y0, color=WHITE, background=BLACK):
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
           if font.flag == 'gb16':
               self._text_gb16(font,size, text, x0, y0, color, background)
               #print('gb16')
           elif font.WIDTH == 8:
               self._text8(font, text, x0, y0, color, background)
           else:
               self._text16(font, text, x0, y0, color, background)
               #print('abc16')
   ```

   

### 4.4、获取中文字体

在线取模网址：[在线点阵取模_暮光小猿wzt (scraft.top)](http://www.scraft.top/tools/lattice/)

首先选择需要的字体大小，底下参数选择**反转位序**

在font_gb_16x16.py中添加字典

示例格式：（**必须标明字体宽高和每个字的字节大小**）

```python
FONT = {
    'HEIGHT':16,
    'WIDTH':16,
    'SIZE':32,
    '当':[0x01,0x00,0x21,0x08,0x11,0x08,0x09,0x10,0x09,0x20,0x01,0x00,0x7f,0xf8,0x00,0x08,0x00,0x08,0x00,0x08,0x3f,0xf8,0x00,0x08,0x00,0x08,0x00,0x08,0x7f,0xf8,0x00,0x08],
    '前':[0x10,0x10,0x08,0x10,0x08,0x20,0xff,0xfe,0x00,0x00,0x3e,0x08,0x22,0x48,0x22,0x48,0x3e,0x48,0x22,0x48,0x22,0x48,0x3e,0x48,0x22,0x08,0x22,0x08,0x2a,0x28,0x24,0x10],
    '天':[0x00,0x00,0x3f,0xf8,0x01,0x00,0x01,0x00,0x01,0x00,0x01,0x00,0xff,0xfe,0x01,0x00,0x02,0x80,0x02,0x80,0x04,0x40,0x04,0x40,0x08,0x20,0x10,0x10,0x20,0x08,0xc0,0x06],
    '气':[0x10,0x00,0x10,0x00,0x3f,0xfc,0x20,0x00,0x4f,0xf0,0x80,0x00,0x3f,0xf0,0x00,0x10,0x00,0x10,0x00,0x10,0x00,0x10,0x00,0x10,0x00,0x0a,0x00,0x0a,0x00,0x06,0x00,0x02],
    '阴':[0x00,0x00,0x7d,0xfc,0x45,0x04,0x49,0x04,0x49,0x04,0x51,0xfc,0x49,0x04,0x49,0x04,0x45,0x04,0x45,0xfc,0x45,0x04,0x69,0x04,0x52,0x04,0x42,0x04,0x44,0x14,0x48,0x08],
    }
```

注：不要加载太多字体，否则会显示内存不足。需要大量字库的话可以将字节码写入文件里，不要用python字典存储，python字典的散列表很耗费空间。

## 五、示例程序

首先将字体文件下载到esp32的flash里，这里我放在了esp32的package文件夹里

```python
from machine import Pin, SPI
from package import st7789py as st
from package import vga1_16x32 as font
from package import font_gb_16x16 as font_gb
import time

class Display():
    def __init__(self):
        self.tft = st.ST7789(SPI(2, 10000000), 240, 240, reset=Pin(17), dc=Pin(2), cs=Pin(5), backlight=Pin(22), rotation=0)
        self.WHITE = st.color565(255, 255, 255)#BRG
        self.BLACK = st.color565(0, 0, 0)
        self.RED = st.color565(0, 255, 0)
        self.GREEN = st.color565(0, 0, 255)
        self.BLUE = st.color565(255, 0, 0)
        self.YELLOW = st.color565(0, 255, 255)
        print(self.RED,self.GREEN,self.BLUE)
        self.last_hour = 0
        self.last_minute = 0
        self.last_second = 0
        self.last_year = 0
        self.last_month = 0
        self.last_day = 0
        self.init_show()
    def init_show(self):
        '''
        初始化显示画面
        '''
        self.tft.text_gb48(font_gb,32, ':', 20+24*2, 100, self.WHITE, self.BLACK)
        self.tft.text_gb48(font_gb,32, ':', 20+24*5, 100, self.WHITE, self.BLACK)
        self.tft.text_gb48(font_gb,32, '00', 20, 100, self.WHITE, self.BLACK)
        self.tft.text_gb48(font_gb,32, '00', 20+24*3, 100, self.WHITE, self.BLACK)
        self.tft.text_gb48(font_gb,32, '00', 20+24*6, 100, self.WHITE, self.BLACK)
        self.text_gb('小雨')
        self.text('hello world!')
    def text_gb(self,text):
        self.tft.text_gb32(font_gb,32, text, 0, 0, self.WHITE, self.BLACK)
    def text(self,text):
        self.tft.text(font,32, text, 0, 50, self.GREEN, self.BLACK)
    
    def show_time(self,t):
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
            self.tft.text_gb48(font_gb,32, '{:0>2d}'.format(hour), 20, 100, self.BLUE, self.BLACK)
            self.last_hour = hour
        if minute != self.last_minute:
            self.tft.text_gb48(font_gb,32, '{:0>2d}'.format(minute), 20+24*3, 100, self.RED, self.BLACK)
            self.last_minute = minute
        if second != self.last_second:
            self.tft.text_gb48(font_gb,32, '{:0>2d}'.format(second), 20+24*6, 100, self.GREEN, self.BLACK)
            self.last_second = second
        #self.tft.text_gb48(font_gb,32, ti, 20, 100, self.WHITE, self.BLACK)
        
    def run(self):
        while True:
            t = time.localtime(time.time())
            #if t[5]%2==0:
            self.show_time(t)
            time.sleep(0.5)
            #for i in range(65536,100):
            #    self.tft.text_gb32(font_gb,32, '雨', 100, 150, i, self.BLACK)
        
    def __del__(self):
        pass
D = Display()
D.run()
```

运行结果见开头
