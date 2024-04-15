import numpy as np
import netCDF4 as nc
import os
from osgeo import gdal, osr
def cumsum_method(pre_array, missing_value, threshold_ratio):
    final_result = np.full((pre_array.shape[1],pre_array.shape[2],4),-999.0,dtype=np.float32)
    pre_array1 = np.where(pre_array == missing_value, 0 , pre_array)
    cumulative_sum = np.cumsum(pre_array1, axis=0)
    total_sum = np.sum(pre_array1, axis=0)
    cumulative_ratio = np.divide(cumulative_sum, total_sum[None, :, :])
    bool_array1 = cumulative_ratio > threshold_ratio
    bool_array2 = cumulative_ratio > 1-threshold_ratio
    final_result[:,:,0] = np.argmax(bool_array1, axis=0) + 1
    final_result[:,:,1] = np.argmax(bool_array2, axis=0) + 1
    final_result[:,:,2] = final_result[:,:,1]-final_result[:,:,0]+1
    for i in range(final_result[:,:,0].shape[0]):
        for j in range(final_result[:, :, 0].shape[1]):
            if final_result[i,j,0] ==1 and final_result[i,j,1] ==1:
                final_result[i, j, 3] = 1
            else:
                final_result[i, j, 3] =cumulative_sum[int(final_result[i,j,1])-1,i,j] -cumulative_sum[int(final_result[i,j,0]-2),i,j]
    return final_result
def get_trans(file_path):
    data = nc.Dataset(file_path, 'r')
    Lon = data.variables['lon'][:]
    Lat = data.variables['lat'][:]
    LonMin, LatMax, LonMax, LatMin = [Lon.min(), Lat.max(), Lon.max(), Lat.min()]
    Lon_Res = (LonMax - LonMin) / (float(len(Lon)) - 1)
    Lat_Res = (LatMax - LatMin) / (float(len(Lat)) - 1)
    trans = (LonMin, Lon_Res, 0, LatMax, 0, -Lat_Res)
    data = None
    return trans

def process_year(file_path, year, threshold_ratio, sub_dir_path, trans):
    with nc.Dataset(file_path) as dataset:
        # 获取时间变量，假设其变量名为'time'
        time_var = dataset.variables['time']
        precipitation_var = dataset.variables['pre']
        lon_list = len(dataset.dimensions['lon'])
        lat_list = len(dataset.dimensions['lat'])

        # 将数值时间转换为日期时间
        times = nc.num2date(time_var[:], units=time_var.units, calendar=time_var.calendar)

        # 找到该年份的时间索引
        year_indices = [i for i, t in enumerate(times) if t.year == year]

        # 提取这一年的降水数据
        year_precipitation = np.array(precipitation_var[year_indices, :, :])
        mis_value = dataset.variables['pre']._FillValue
        print(f"{year}数据运行中")
        result = cumsum_method(year_precipitation, mis_value, threshold_ratio)
        filename1 = f'{year}_cum{threshold_ratio}_result.tif'
        result_path1 = os.path.join(sub_dir_path, filename1)

        # result2 = np.transpose(result, (1, 0))
        result2 = result[::-1, :,:]
        result1 = np.where(result2 == 1,-999, result2)
        # 栅格文件写入部分
        driver = gdal.GetDriverByName("GTiff")
        datasetnew1 = driver.Create(result_path1, lon_list, lat_list, result1.shape[2], gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # 定义输出的坐标系为"WGS 84"，AUTHORITY["EPSG","4326"]
        datasetnew1.SetGeoTransform(trans)
        datasetnew1.SetProjection(srs.ExportToWkt())
        nodata = -999
        for i in range(1,result1.shape[2]+1):
            datasetnew1.GetRasterBand(i).WriteArray(result1[:, :,i-1])
            datasetnew1.GetRasterBand(i).SetNoDataValue(nodata)
            datasetnew1.FlushCache()  # Write to disk
        datasetnew1 = None

def process(start_year, end_year, file_path, threshold_ratio, sub_dir):
    trans = get_trans(file_path)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sub_dir_path = os.path.join(current_dir, sub_dir)
    if not os.path.exists(sub_dir_path):
        os.makedirs(sub_dir_path, exist_ok=True)

    # 创建阈值对应的子文件夹
    threshold_dir = os.path.join(sub_dir_path, str(threshold_ratio))
    if not os.path.exists(threshold_dir):
        os.makedirs(threshold_dir, exist_ok=True)

    for year in range(start_year, end_year+1):
        process_year(file_path, year, threshold_ratio, threshold_dir, trans)

if __name__ == "__main__":
    start_year=1982
    end_year=2022
    file_path=r"D:\phenology_pycode\new_data_files\CN05.1_Pre_1961_2022_daily_025x025.nc"
    threshold_ratio1 = [0.1,0.15,0.2,0.25,0.3]   # 阈值的列表，输入数字即可
    result_path = "./new_data_files/cum_result"  # 输出文件的文件夹名
    for i in threshold_ratio1:
        process(start_year, end_year, file_path, i,result_path)
