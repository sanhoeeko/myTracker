import sys
import os
import cv2 as cv
import copy as cp
import math as mh
import pandas as pd

import numpy as np
import time as tt
from PyQt5.Qt import *
from PyQt5 import QtWidgets
from magicWand import wand, search

w_over_h = 20 / 9
h = 720  # 必须是9的倍数，否则图像显示出错或报段错误0xC0000005
w = int(h * w_over_h)
shift = 5
step = 0
img = None
img_cache = None
img_stable = None
texts = ['1.这张图片？',
         '2.请选择圆心',
         '3.请选择x轴单位点',
         '4.请选择球上一点',
         '5.这个轨迹合理吗？',
         '已保存。']
pics = []
save_turns = 0 #唯一不能重新初始化的变量
src_dir = None
max_time = 5


def sortHash(filename):  # format: Image<int>
    lis = filename.split('.')
    name = lis[0]
    numStr = name[5:]
    num = int(numStr)
    return num


def init(path):
    global pics
    for root, dirs, files in os.walk(path):
        files.sort(key=sortHash)
        for file in files:
            pics.append(path + '/' + file)
    cvRead(pics[0])


def cvRead(path):
    global img
    img = cv.imread(path)  # 读取图像
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)  # 转换图像通道
    img = cv.resize(img, (w, h))


def cvRead_return(path):
    res = cv.imread(path)  # 读取图像
    res = cv.cvtColor(res, cv.COLOR_BGR2RGB)  # 转换图像通道
    res = cv.resize(res, (w, h))
    return res


def mouse():
    pos = QCursor.pos()
    return pos.x(), pos.y()


def hueMat(pic):  # 获取图像的色调，这个最适合识别玻璃球
    mat = cv.cvtColor(pic, cv.COLOR_BGR2HSV)
    return mat[:, :, 0]


def maskRed(mask):
    global img_cache  # 要联系上下文，不能修改img！
    m, n, _ = img.shape
    for i in range(m):
        for j in range(n):
            if mask[i, j]:
                img_cache[i, j, 1] = 0
                img_cache[i, j, 2] = 0


class Data:
    def __init__(self):
        self.center = None
        self.x_unit_point = None
        self.lis = [None]
        self.ihue = None
        self.res = None

    def cal(self):
        vecs = np.array(self.lis).T  # 列向量组
        origin = np.array([self.center]).T
        a = np.array([self.x_unit_point]).T
        vecs -= origin
        a -= origin
        r = np.linalg.norm(a)
        vecs = vecs.astype(float)
        vecs /= r
        th = mh.atan2(a[1, 0], a[0, 0])
        D = np.array([[mh.cos(th), -mh.sin(th)],
                      [mh.sin(th), mh.cos(th)]]).T
        self.res = D @ vecs

    def save(self):
        global save_turns
        self.cal()
        mat = self.res
        frame = pd.DataFrame({'x': mat[0], 'y': mat[1]})
        filename='output/'+str(src_dir)+'_result_'+str(save_turns)+'.csv'
        save_turns+=1
        frame.to_csv(filename, index=False, sep=',')

    def draw(self, pic):
        a = 5
        for pos in self.lis:
            x, y = pos[0], pos[1]
            cv.line(pic, (x - a, y - a), (x + a, y + a), (100, 0, 200))
            cv.line(pic, (x + a, y - a), (x - a, y + a), (100, 0, 200))
        for j in range(1, len(self.lis)):
            cv.line(pic, self.lis[j - 1], self.lis[j], (100, 0, 200))
        return pic


data = Data()


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        self.setWindowTitle('myTracker')
        self.resize(2000, 800)

        self.view = QGraphicsView(self)
        self.view.setGeometry(0, 0, w + shift * 2, h + shift * 2)
        self.initImage()
        self.showImage()

        self.butt = QPushButton(self)
        self.butt.move(w + 4 * shift, 200)
        self.butt.setText('OK')
        self.butt.clicked.connect(buttClick)

        self.label = QLabel(self)
        self.label.move(w + 4 * shift, 100)
        self.label.resize(300, 100)
        self.label.setText(texts[step])

        self.b2 = QPushButton(self)
        self.b2.move(w + 4 * shift, 300)
        self.b2.setText('下一张')
        self.b2.clicked.connect(b2Click)

        self.b3 = QPushButton(self)
        self.b3.move(w + 4 * shift, 400)
        self.b3.setText('')
        self.b3.clicked.connect(b3Click)

    def initImage(self):
        global img, img_cache, img_stable
        img_cache = cp.deepcopy(img)
        img_stable = cp.deepcopy(img)

    def showImage(self):
        frame = QImage(img, w, h, QImage.Format_RGB888)
        pix = QPixmap.fromImage(frame)
        self.item = QGraphicsPixmapItem(pix)  # 创建像素图元
        self.scene = QGraphicsScene()  # 创建场景
        self.scene.addItem(self.item)
        self.view.setScene(self.scene)
        self.view.show()

    def mousePressEvent(self, *args):  # *args是事件对象，不重要，但是要有这个坑位
        global data
        if step == 1:
            x, y = mouse()
            draw_x(x - 13, y - 42, (255, 0, 0))  # 魔法数字，勿动！
            data.center = (x - 13, y - 42)
            self.showImage()
        elif step == 2:
            x, y = mouse()
            draw_x(x - 13, y - 42, (0, 0, 255))  # 魔法数字，勿动！
            data.x_unit_point = (x - 13, y - 42)
            self.showImage()
        elif step == 3:
            x, y = mouse()
            mat = hueMat(img_stable)
            pts, mask, mean_hue = wand(mat, y - 42, x - 13)
            data.ihue = mean_hue
            pts = np.array(pts)
            n = pts.shape[0]
            heart = np.sum(pts, axis=0) / n
            x0, y0 = round(heart[1]), round(heart[0])
            print(x0, y0)
            maskRed(mask)
            draw_x(x0, y0, (0, 255, 0))
            data.lis[0] = (x0, y0)
            self.showImage()


def buttClick():
    global step, pics
    if work():
        step += 1
        if step <= 5:
            ui.label.setText(texts[step])
        if step == 4:
            ui.butt.setText('保存')
            ui.b2.setText('不合理，重来')
            ui.b3.setText('检查下一张')
        if step == 5:
            data.save()
            ui.butt.setText('继续')
        if step == 6:
            pics = pics[len(data.lis):]
            step = 0
            clear_all()


def b2Click():
    global pics, step
    if step == 0:
        pics = pics[1:]
        cvRead(pics[0])
        ui.initImage()
        ui.showImage()
    if step == 4:
        step = 0
        clear_all()


pic_ptr = 0


def b3Click():
    global pic_ptr, img
    if step == 4:
        pic_ptr += 1
        cvRead(pics[pic_ptr])
        img = data.draw(img)
        ui.initImage()
        ui.showImage()


def work():
    global img, img_cache
    if step == 1:
        img_cache = cp.deepcopy(img)
    if step == 2:
        img_cache = cp.deepcopy(img)
    if step == 3:
        # 开始追踪小球
        i = 1
        t_cache=tt.time() # 此处容易超时
        while searchRGB(pics[i]):
            t=tt.time()
            i += 1
            if i >= len(pics): break
            if t-t_cache > max_time:break
            t_cache = t
        # 画出轨迹
        for pos in data.lis:
            print(pos)
            draw_x_unsafe(pos[0], pos[1], (100, 0, 200))
        for j in range(1, len(data.lis)):
            cv.line(img, data.lis[j - 1], data.lis[j], (100, 0, 200))
        ui.showImage()
    return True


def draw_x(x, y, color):
    global img
    img = cp.deepcopy(img_cache)
    a = 10
    cv.line(img, (x - a, y - a), (x + a, y + a), color)
    cv.line(img, (x + a, y - a), (x - a, y + a), color)


def draw_x_unsafe(x, y, color):
    global img
    a = 5
    cv.line(img, (x - a, y - a), (x + a, y + a), color)
    cv.line(img, (x + a, y - a), (x - a, y + a), color)


def searchRGB(pic_path):
    global data
    mat = hueMat(cvRead_return(pic_path))
    pts, _, _ = search(mat, data.ihue, data.lis[-1][0], data.lis[-1][1])
    if pts is None: return False  # 没有找到小球，返回异常值
    pts = np.array(pts)
    n = pts.shape[0]
    heart = np.sum(pts, axis=0) / n
    x0, y0 = round(heart[1]), round(heart[0])
    data.lis.append((x0, y0))
    return True


def clear_all():
    global data, pic_ptr
    data = Data()
    pic_ptr = 0
    cvRead(pics[0])
    ui.initImage()
    ui.showImage()
    ui.butt.setText('OK')
    ui.b2.setText('下一张')
    ui.b3.setText('')
    ui.label.setText(texts[0])
    
def start_halfway(num, picNum):
    global pics, save_turns
    save_turns = num
    pics = pics[picNum:]


if __name__ == '__main__':
    src_dir = '48'
    init(src_dir)
    start_halfway(0,0)
    app = QtWidgets.QApplication(sys.argv)
    ui = UI()
    ui.show()
    sys.exit(app.exec())
