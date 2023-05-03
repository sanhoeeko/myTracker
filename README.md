# myTracker

用于保罗机械阱物理实验，只要拍摄小球运动的视频并分帧，就可以自动找出小球的位置并输出数据。  

为了尽可能排除拍摄角度的影响，相机应固定并正对机械阱所在平面，在机械阱上画上一些坐标以便将图距（像素）转换为实际距离（cm）。

### 使用注意：

1. 请将图片序列放在`test/`文件夹下，并以`Image1, Image2, ...`命名，推荐用格式工厂分帧。（否则，可以修改图片按文件名排序相关的代码）
2. 面向玻璃球编程，钢球等不知能否使用
3. 检测精度一般，耗时倒是很久，动不动就crash（更新：添加了超时检测后基本上不会crash了）
4. 操作方法见视频

### 其他的话：

去年的项目了，当时写Qt很生疏，还不知道UI和后端处理分离，因此它们是耦合的……以后千万不要这么干。
