# 单片机实现utf-8转gb2312

 我们在单片机开发中常会遇到需要将UTF-8转换为GBK编码的需求。在了解各种编码格式的情况下可知， UFT-8不能直接转成GBK，需中转成unicode再转换为gbk。而unicode和gbk之间没有算法可以直接计算，需要查表方式获取。

网上有一些C语言实现的代码，我这里分享一种microPython的实现代码

接下来就是要考虑表的存储方式了，刚开始我想着把表存到代码里直接通过索引实现编码转换。但是gb2312有七千多个字符全部存储要耗费很大内存，即使是32位的esp32也只有512k的内存，加上其他资源的消耗，剩余的内存不足以存储编码转换表。

于是只能将表保存成一个文件（转化成bin文件会比较好，方法类似），通过读写文件来减少内存开销。

具体的查表就是简单的二分法


## 代码实现：

```python
class utf8_gb2312(object):
    def __init__(self):
        self.f = open('font.txt', 'r', encoding='utf-8')

    def b2i(self, byte):  # bytes转int
        r = 0
        for i in range(len(byte)):
            r = (r << 8) + byte[i]
        return r

    def i2b(self, num):  # int转bytes
        num = int(num, 16)
        return num.to_bytes(2, 'big')

    def one_char(self, char):  # 将一个字符转化成gb2312
        utf_byte = char.encode('utf-8')
        r = self.B_S(0, 7296, self.b2i(utf_byte))
        gb2312_byte = self.i2b(r)
        # print(gb2312_byte)
        return gb2312_byte

    def str(self, st):  # 将字符串转化成gb2312
        r = b''
        for s in st:
            # print(s.encode('utf-8'))
            if len(s.encode('utf-8')) <= 1:
                r += s.encode('utf-8')
            else:
                r += self.one_char(s)
        return r

    def B_S(self, low, high, m):  # 二分查找
        if 0 <= low <= high <= 7296:
            mid = (low + high) // 2
            self.f.seek(mid * 12)
            data = self.f.read(12)
            utf = data[0:6]
            if int(utf, 16) < m:
                return self.B_S(mid + 1, high, m)
            elif int(utf, 16) > m:
                return self.B_S(low, mid - 1, m)
            else:
                return data[7:-1]

    def __del__(self):
        self.f.close()


if __name__ == '__main__':
    font = utf8_gb2312()
    r = font.one_char('起')
    print(r.decode('gb2312'))
    r = font.str('起风了Abc123-')
    print(r)
    print(r.decode('gb2312'))
```

## 附件下载地址：

https://github.com/LC044/MCU
