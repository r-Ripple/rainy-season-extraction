import netCDF4 as nc
import func_repairing as ft
import numpy as np
from osgeo import gdal, osr
from scipy.stats import t
import multiprocessing
import os


# 函数用于处理给定年份的数据
def process_year(file_path, year, lat_list, lon_list, window, mis_value, t_list, trans,sub_dir):
    with nc.Dataset(file_path) as dataset:
        # 获取时间变量，假设其变量名为'time'
        time_var = dataset.variables['time']
        precipitation_var = dataset.variables['pre']

        # 将数值时间转换为日期时间
        times = nc.num2date(time_var[:], units=time_var.units, calendar=time_var.calendar)

        # 找到该年份的时间索引
        year_indices = [i for i, t in enumerate(times) if t.year == year]

        # 提取这一年的降水数据
        year_precipitation = np.array(precipitation_var[year_indices, :, :])

        print(f"{year}数据运行中")
        result = ft.array_rs_index(year_precipitation, lat_list, lon_list, window, mis_value, t_list, year)

        # 获取当前脚本所在的目录
        current_dir = os.path.dirname(os.path.abspath(__file__))


        sub_dir_path = os.path.join(current_dir, sub_dir)
        if not os.path.exists(sub_dir_path):
            os.makedirs(sub_dir_path, exist_ok=True)
        # 定义子文件名
        filename1 = f'{year}_result.tif'
        filename2 = f'{year}_result_array'
        result_path1 = os.path.join(sub_dir_path, filename1)
        array_path = os.path.join(sub_dir_path,filename2)
        np.save(array_path, result)

        result2 = np.transpose(result, (1, 0, 2))
        result1 = result2[::-1, :, :]

        # 栅格文件写入部分
        driver = gdal.GetDriverByName("GTiff")
        datasetnew1 = driver.Create(result_path1, lon_list, lat_list, 4, gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # 定义输出的坐标系为"WGS 84"，AUTHORITY["EPSG","4326"]
        datasetnew1.SetGeoTransform(trans)
        datasetnew1.SetProjection(srs.ExportToWkt())
        nodata = -999.0
        for i in range(1, 5):
            datasetnew1.GetRasterBand(i).WriteArray(result1[:, :, i - 1])
            datasetnew1.GetRasterBand(i).SetNoDataValue(nodata)
        datasetnew1.FlushCache()  # Write to disk
        datasetnew1 = None



# 使用多进程处理每年的数据
def process_all_years(file_path, start_year, end_year, lat_list, lon_list, window, mis_value ,t_list ,trans,sub_dir):
    # 创建进程池
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    cpu = multiprocessing.cpu_count()
    print(f"正在执行多进程，cpu数：{cpu}")

    # 构建启动进程的参数列表，每个年份一个参数
    args = [(file_path, year, lat_list, lon_list, window, mis_value, t_list, trans,sub_dir) for year in range(start_year, end_year + 1)]

    # 启动多进程计算
    results = pool.starmap(process_year, args)
    pool.close()
    pool.join()

    return results



if __name__ == '__main__':
    file_path = r"D:\phenology_pycode\new_data_files\CN05.1_Pre_1961_2022_daily_025x025.nc"
    start_year = 1982
    end_year = 2022
    sub_dir = 't_result'
    # 上面三项为基本的待修改参数


    t_list = t.ppf(0.99, range(30, 183))
    window = np.array(range(30, 183))
    # 这两项是相互对应的，在滑动t检验中若改变需要同步改变

    data = nc.Dataset(file_path, 'r')
    data.set_auto_mask(False)
    Lon = data.variables['lon'][:]
    Lat = data.variables['lat'][:]
    LonMin, LatMax, LonMax, LatMin = [Lon.min(), Lat.max(), Lon.max(), Lat.min()]
    Lon_Res = (LonMax - LonMin) / (float(len(Lon)) - 1)
    Lat_Res = (LatMax - LatMin) / (float(len(Lat)) - 1)
    trans = (LonMin, Lon_Res, 0, LatMax, 0, -Lat_Res)
    lon_len = len(data.dimensions['lon'])
    lat_len = len(data.dimensions['lat'])
    mis_value = data.variables['pre']._FillValue
    data.close()

    results = process_all_years(file_path, start_year, end_year, lat_len, lon_len, window, mis_value ,t_list ,trans,sub_dir)
