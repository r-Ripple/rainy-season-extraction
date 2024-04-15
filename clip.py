from osgeo import gdal
import numpy as np
import time
import re
import os
from multiprocessing import Process, cpu_count

def get_valid_intersection(file_path, target_path, output_path):
    # 打开第一个 TIF 文件
    ds1 = gdal.Open(file_path)
    band1 = ds1.GetRasterBand(1)
    data1 = band1.ReadAsArray()
    nodata1 = band1.GetNoDataValue()
    geotransform1 = ds1.GetGeoTransform()
    projection1 = ds1.GetProjection()

    # 打开第二个 TIF 文件
    ds2 = gdal.Open(target_path)
    band2 = ds2.GetRasterBand(1)
    data2 = band2.ReadAsArray()
    nodata2 = band2.GetNoDataValue()

    # 找到两个 TIF 文件中都有有效值的位置
    valid_mask = (data1 != nodata1) & (data2 != nodata2)

    # 获取有效值交集
    valid_intersection = np.where(valid_mask, data1, nodata1)

    # 创建新的 TIF 文件
    driver = gdal.GetDriverByName('GTiff')
    output_ds = driver.Create(output_path, ds1.RasterXSize, ds1.RasterYSize, 1, gdal.GDT_Float32)
    output_ds.SetProjection(projection1)
    output_ds.SetGeoTransform(geotransform1)
    output_band = output_ds.GetRasterBand(1)
    output_band.SetNoDataValue(nodata1)
    output_band.WriteArray(valid_intersection)
    output_band.FlushCache()

    # 关闭数据集
    ds1 = None
    ds2 = None
    output_ds = None

def create_dir(dirname):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sub_dir_path = os.path.join(current_dir, dirname)
    if not os.path.exists(sub_dir_path):
        os.makedirs(sub_dir_path, exist_ok=True)
    return sub_dir_path

def get_tifs(path):
    files = os.listdir(path)
    tifs = []
    for file in files:
        if file.endswith('.tif'):
            tifs.append(os.path.join(path, file))
    return tifs

def get_filename(filename):
    pattern = r"(\d{1,5})_res.*?\.tif"
    match = re.search(pattern, filename)
    i = 0
    if match:
        num = match.group(1)
        new_filename = f"res_clip_{num}.tif"
        return new_filename
    else:
        i += 1
        aa = f"error{i}"
        return aa

def process_subset(target, tifs, subdir, start_index, end_index):
    sub_dir_path = create_dir(subdir)
    j = start_index
    for tif in tifs[start_index:end_index]:
        j += 1
        filename = get_filename(os.path.basename(tif))
        output_path = os.path.join(sub_dir_path, filename)
        get_valid_intersection(tif, target, output_path)
        if j % 100 == 0:
            print(f"进程{os.getpid()}: 已处理{j}个文件")
    print(f"进程{os.getpid()}: 共处理{j - start_index}个文件")

def process(target, file_path, subdir):
    tifs = get_tifs(file_path)
    num_processes = cpu_count()
    chunk_size = len(tifs) // num_processes

    processes = []
    for i in range(num_processes):
        start_index = i * chunk_size
        end_index = (i + 1) * chunk_size if i < num_processes - 1 else len(tifs)
        process = Process(target=process_subset, args=(target, tifs, subdir, start_index, end_index))
        processes.append(process)
        process.start()

    for process in processes:
        process.join()


if __name__ == "__main__":
    start_time = time.time()
    target = r"C:\Users\15824\Desktop\1982NDVI生长季结束.tif"
    file_path = r"D:\semester six\aaa"
    subdir = "clip_test"
    process(target, file_path, subdir)


    end_time = time.time()
    duration = end_time - start_time
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)

    print("程序运行时间：{}小时{}分钟{}秒".format(hours, minutes, seconds))

