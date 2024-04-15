import netCDF4 as nc
import numpy as np
import os
from osgeo import gdal,osr


def process_year(file_path, year):
    with nc.Dataset(file_path) as dataset:
        # 获取时间变量，假设其变量名为'time'
        time_var = dataset.variables['time']
        precipitation_var = dataset.variables['pre']
        nodata_value = dataset.variables['pre']._FillValue


        times = nc.num2date(time_var[:], units=time_var.units, calendar=time_var.calendar)
        year_indices = [i for i, t in enumerate(times) if t.year == year]


        year_precipitation = np.array(precipitation_var[year_indices, :, :])
        result = np.full((year_precipitation.shape[1], year_precipitation.shape[2], 4), -999.0, dtype=np.float32)
        year_precipitation[year_precipitation == nodata_value] = np.nan
        print(f"{year}数据运行中")


        avg_pre = np.nanmean(year_precipitation, axis=0)
        differ_pre = year_precipitation - np.broadcast_to(avg_pre, year_precipitation.shape)
        cum_pre = np.cumsum(differ_pre, axis=0)
        cumulative_sum =np.cumsum(year_precipitation, axis=0)

        for i in range(result.shape[0]):
            for j in range(result.shape[1]):
                if not np.isnan(cum_pre[:, i, j]).all():  # 如果不是全部为NaN
                    # 计算最大累积降水日（nanargmax将返回第一个出现的最大值的索引）
                    result[i, j, 1] = np.nanargmax(cum_pre[:, i, j]) + 2
                    # 计算最小累积降水日（nanargmin将返回第一个出现的最小值的索引）
                    result[i, j, 0] = np.nanargmin(cum_pre[:, i, j]) + 2
                    result[i, j, 2] = np.nanargmax(cum_pre[:, i, j]) - np.nanargmin(cum_pre[:, i, j]) +1
                    result[i, j, 3] =cumulative_sum[int(result[i,j,1])-2,i,j] -cumulative_sum[int(result[i,j,0]-3),i,j]
    return result


def process(file_path,start_year,end_year,sub_dir):
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


    for year in range(start_year, end_year + 1):
        result = process_year(file_path, year)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sub_dir_path = os.path.join(current_dir, sub_dir)
        if not os.path.exists(sub_dir_path):
            os.makedirs(sub_dir_path, exist_ok=True)
        filename1 = f'{year}_AA_result.tif'
        result_path1 = os.path.join(sub_dir_path, filename1)

        # result2 = np.transpose(result, (1, 0, 2))
        result1 = result[::-1, :, :]

        # 栅格文件写入部分
        driver = gdal.GetDriverByName("GTiff")
        datasetnew1 = driver.Create(result_path1, lon_len, lat_len, result1.shape[2], gdal.GDT_Float32)
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)  # 定义输出的坐标系为"WGS 84"，AUTHORITY["EPSG","4326"]
        datasetnew1.SetGeoTransform(trans)
        datasetnew1.SetProjection(srs.ExportToWkt())
        nodata = -999.0
        for i in range(1, result1.shape[2]+1):
            datasetnew1.GetRasterBand(i).WriteArray(result1[:, :, i - 1])
            datasetnew1.GetRasterBand(i).SetNoDataValue(nodata)
        datasetnew1.FlushCache()
        datasetnew1 = None

if __name__ == "__main__":
    start_year = 1982
    end_year = 2022
    file_path = r"D:\phenology_pycode\new_data_files\CN05.1_Pre_1961_2022_daily_025x025.nc"
    sub_dir = "./new_data_files/AA_result"
    # 上面三项为基本的待修改参数
    process(file_path, start_year, end_year, sub_dir)


