# 功能代码，可修改的地方是开始和结束的经验筛选方法
# 四层分别是： 雨季开始 雨季结束 雨季长度 雨季长度内的降水量
import numpy as np
from numba import njit




@njit
def sam_var(data):
    mean = np.mean(data)
    squared_diff_sum = np.sum((data - mean) ** 2)

    n = len(data)
    if n < 2:
        return np.nan

    sample_variance = squared_diff_sum / (n - 1)
    return sample_variance
@njit
def array_rs_index(precipitation_data_year, lat_list, lon_list, window_sizes, mis_value, t_list, year):
    result= np.empty((lon_list, lat_list,4), dtype=np.float32)

    total = lat_list * lon_list
    count = 0

    for lat in range(lat_list):
        for lon in range(lon_list):
            count += 1
            if count % 5000 == 0 or count == total:  # 每100次迭代更新一次，或者在最后一次迭代时更新
                print(year, count, total)
                print(lat,lon)


            precipitation_data = precipitation_data_year[:,lat,lon]
            cumsum_pre = np.cumsum(precipitation_data)
            if precipitation_data[0] == mis_value:
                result[lon,lat,:]= -999.0
            else:
                max_normalized_t = -np.inf
                min_normalized_t = np.inf
                start_index = -1
                end_index = 1
                final_window_start = -999.0
                final_window_end = -999.0

                for window_size in window_sizes:
                    df = window_size  # 自由度
                    # t_critical = t.ppf(0.99, df)  # 置信度为 0.01 的 t 检验临界值
                    t_critical = t_list[df-30]

                    for i in range(len(precipitation_data) - 2* window_size - 1):
                        window1 = precipitation_data[i:i + window_size]
                        window2 = precipitation_data[i + window_size + 1:i + 2 * window_size + 1]

                        mean_window1 = np.mean(window1)
                        mean_window2 = np.mean(window2)
                        std_window1 = sam_var(window1)
                        std_window2 = sam_var(window2)
                        # a_std_window1 = std_window1[0]
                        # a_std_window2 = std_window2[0]

                        if window_size > 1:
                            # 如果窗口1和窗口2的标准差都为0，则跳过当前循环
                            if std_window1 == 0 and std_window2 == 0:
                                continue
                            min_nonzero_value = np.array([1e-9])
                            a_std_window1 = np.maximum(std_window1, min_nonzero_value)
                            a_std_window2 = np.maximum(std_window2, min_nonzero_value)

                            t_value = (mean_window2 - mean_window1) / np.sqrt((std_window2) + (std_window1)) * np.sqrt(window_size)
                            normalized_t = t_value / t_critical


                            if normalized_t > max_normalized_t:
                                if i + window_size < 181:           # 雨季开始在180天前
                                    max_normalized_t = normalized_t
                                    start_index = i + window_size
                                    final_window_start = df
                            if normalized_t < min_normalized_t:
                                if i + window_size > 180:           # 雨季结束在180天前
                                    min_normalized_t = normalized_t
                                    end_index = i + window_size
                                    final_window_end = df

                result[lon, lat, 0] = start_index+1
                result[lon, lat, 1] = end_index+1
                result[lon, lat, 2] = end_index - start_index +1
                result[lon, lat, 3] = cumsum_pre[end_index] - cumsum_pre[start_index-1]

    return result