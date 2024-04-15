from osgeo import gdal, osr
import os
import re
import time
def resample_tif(low_res_tif_path, high_res_tif_path, resampled_tif_path):
    # Open the low resolution and high resolution images
    low_res_ds = gdal.Open(low_res_tif_path, gdal.GA_ReadOnly)
    high_res_ds = gdal.Open(high_res_tif_path, gdal.GA_ReadOnly)

    # Get the projection and geotransform of the low resolution image
    low_res_proj = low_res_ds.GetProjection()
    low_res_geotrans = low_res_ds.GetGeoTransform()

    # Get the resolution (pixel size) of the high resolution image

    high_res_geotrans = high_res_ds.GetGeoTransform()

    # Calculate the size of the resampled image
    x_size = high_res_ds.RasterXSize
    y_size = high_res_ds.RasterYSize

    # Set the geotransform of the output image to align with the high resolution image
    out_geotrans = list(high_res_geotrans)
    #out_geotrans[1] = x_res  # Set the pixel width
    #out_geotrans[5] = y_res  # Set the pixel height

    # Get the number of bands
    num_bands = low_res_ds.RasterCount

    # Create the output image
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(resampled_tif_path, x_size, y_size,
                           num_bands, low_res_ds.GetRasterBand(1).DataType)
    out_ds.SetProjection(low_res_proj)
    out_ds.SetGeoTransform(out_geotrans)

    # Perform the resampling for each band
    for band in range(1, num_bands + 1):
        # Get the corresponding band
        in_band = low_res_ds.GetRasterBand(band)
        out_band = out_ds.GetRasterBand(band)

        # Reproject the band
        gdal.ReprojectImage(low_res_ds, out_ds,
                            low_res_proj, high_res_ds.GetProjection(),
                            gdal.GRA_Bilinear)
        out_ds.GetRasterBand(band).SetNoDataValue(0.0)

        # Flush the band's data to disk
        out_band.FlushCache()

    # Close the datasets
    out_ds = None
    low_res_ds = None
    high_res_ds = None
def create_dir(dirname):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sub_dir_path = os.path.join(current_dir, dirname)
    if not os.path.exists(sub_dir_path):
        os.makedirs(sub_dir_path, exist_ok=True)
    return sub_dir_path
def process(highres_file,low_path,result_path,method):
    aa = r'(?<=CN05_)\d{1,5}(?=\.tif)'
    result_full_path = create_dir(result_path)
    for file in os.listdir(low_path):
        # 检查文件扩展名
        if file.endswith('.tif'):
            match = re.search(aa, file)
            if match:
                year = match.group()
                print(f"year: {year}")
                file_path = os.path.join(low_path, file)
                result_name = f"{year}_{method}res.tif"
                resampled_tif_path = os.path.join(result_full_path, result_name)
                resample_tif(file_path, highres_file, resampled_tif_path)
                # print(f"{year}天完成")
            else:
                print("error")




# 使用示例
if __name__ == "__main__":
    start_time = time.time()
    highres_file = r"G:\CN05.1-1961-2022-daily\sp\1982NDVI生长季结束.tif"  # 目标尺度对应的tif文件
    low_path =r"G:\CN05.1-1961-2022-daily\1\11"   # 待转换的tif文件路径
    result_path ="pre_res"   # 输出文件的文件夹名
    method = ""  #  用于标识输出文件的方法名，可以为空
    process(highres_file, low_path, result_path, method)
    end_time = time.time()
    duration = end_time - start_time
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)

    print("程序运行时间：{}小时{}分钟{}秒".format(hours, minutes, seconds))


