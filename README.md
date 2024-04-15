# 雨季提取代码集
ripple.w@qq.com
## 介绍
本代码主要基于三种雨季提取方法，针对以nc文件的降水气象数据进行雨季提取（geotiff文件）以及后续的栅格变尺度和重采样进行实现。
## 依赖包
* numpy
* scipy
* netcdf4
* gdal
* osr
* numba
* multiprocessing
* pymannkendall
* matplotlib
## 三种雨季方法
雨季提取的结果统一为geotiff文件，四层分别是雨季开始 雨季结束 雨季长度 雨季长度内的降水量
### 累积阈值法
对应代码为 cumsum_test.py
在设定子文件夹时，必须保证最底层文件夹的上层文件夹存在

如："./new_data_files/cum_result"中，必须保证对应的"new_data_files"文件夹已被创建
### 异常累积法
对应代码为 AA_method.py

文件夹要求同上
### 多尺度滑动t检验法
多尺度滑动t检验法分为两个模块
* 功能模块 对应代码为 func_repairing.py 封装了基本方法的实现
* 主程序模块 对应代码为 pool version new.py 
## 其他部分
### 变尺度
对应代码为： scale_change.py

可以把某一文件夹的tif文件的投影变为目标tif文件的投影，同时使用二次线性插值进行尺度变化，结果的transform和projection将与目标文件相同

结果的范围与原tif文件范围一致，而非目标tif文件
### 裁剪
对应代码为：clip.py

使用前提是两者transform和projection相同，裁剪逻辑是取两者范围的交集
