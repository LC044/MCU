# SD卡的使用

## 一、接线方式

引脚定义：http://www.micropython.com.cn/en/latet/library/machine.SDCard.html

| SD板 | ESP32开发板 | GPIO |
| :--: | :---------: | :--: |
| GND  |     GND     |      |
| VCC  |     5V      |      |
|  CS  |     G5      |  5   |
| MOSI |     G23     |  23  |
| SCK  |     G18     |  18  |
| MISO |     G19     |  19  |

## 二、示例程序

```python

import framebuf
from machine import Pin, SPI

import machine, os
import sdcard

SD_CS = machine.Pin(15)
spi = machine.SPI(1,sck=Pin(14), mosi=Pin(13),miso=Pin(12))
spi.init()
sd = sdcard.SDCard(spi, SD_CS)
vfs = os.VfsFat(sd)   # 初始化fat文件系统
os.mount(sd, "/sd")   # 挂载SD卡到/sd目录下
dirs=os.listdir('/sd')
for file in dirs:
   print (file)
f = open('/sd/hello.txt','w',encoding='utf-8')
f.write('hello')
f.close()

```

## 三、驱动下载地址

https://github.com/micropython/micropython/blob/master/drivers/sdcard/sdcard.py



