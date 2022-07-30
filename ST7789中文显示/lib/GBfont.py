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
        #num = int(num, 16)
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
        
