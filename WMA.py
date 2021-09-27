# coding: utf-8
# -*- coding: utf-8 -*-
import AuoLogger

logName = '01'
logger = AuoLogger.AUOLog(logName=logName)

import pandas as pd
import numpy as np
import time
import json

with open('WMA.json') as j:
    cfg = json.load(j)
SQC_IN = cfg["SQC_IN"]
ins_dir = cfg["QC_JUDGE"]
area_judge = cfg["AREA_JUDGE"]
pixel_repeat_x = area_judge["pixel_repeat_x"]
pixel_repeat_y = area_judge["pixel_repeat_y"]
area_repeat_x = area_judge["area_repeat_x"]
area_repeat_y = area_judge["area_repeat_y"]
less_ng_cnt = area_judge["less_ng_cnt"]


def create_SQC_file(chip_x=20, chip_y=10, file_path_in="./data/0_SQC_IN/", wafer_area=1,
                    wafer_id="COT#R#LON" + time.strftime("%Y%m%d%H%M%S"), version=0):
    logger.info("start do create_SQC_file ...")
    start = time.time()
    wafer_area = '{0:02d}'.format(wafer_area)
    chip_layout = '{0:04d}'.format(chip_x) + '#' + '{0:04d}'.format(chip_y)
    file_name = wafer_id + '#' + wafer_area + '#' + chip_layout + '#v' + '{0:03d}'.format(version) + '.csv'
    x_no = np.arange(start=1, stop=chip_x + 1, step=1)
    y_no = np.full(chip_x, 1)
    for i in range(chip_y - 1):
        x_no = np.concatenate((x_no, np.arange(start=1, stop=chip_x + 1, step=1)), axis=0)
        y_no = np.concatenate((y_no, np.full(chip_x, i + 2)), axis=0)
    xy_no = np.concatenate((np.expand_dims(y_no, axis=1), np.expand_dims(x_no, axis=1)), axis=1)
    SQC_df = pd.DataFrame(data=xy_no, columns=['x_no', 'y_no'])
    SQC_df['ins_01'] = np.round(np.random.randint(low=4, high=10, size=(chip_x * chip_y)) / 0.97, 2)
    SQC_df['ins_02'] = np.round(np.random.randint(low=5, high=10, size=(chip_x * chip_y)) * 501.11111, 4)
    SQC_df['ins_03'] = np.random.choice([0, 1], size=chip_x * chip_y, p=[0.9, 0.1])
    SQC_df['ins_04'] = np.round(np.random.normal(10, 1, size=chip_x * chip_y), 4)
    SQC_df['ins_05'] = np.round(np.random.normal(4000, 203, size=chip_x * chip_y), 4)
    SQC_df['ins_06'] = np.round(np.random.normal(4300, 633, size=chip_x * chip_y), 4)
    SQC_df['ins_07'] = np.round(np.random.normal(4600, 37, size=chip_x * chip_y), 4)
    SQC_df = SQC_df.sort_values(by=['x_no', 'y_no'], ascending=[True, True]).reset_index(drop=True)
    SQC_df.to_csv(file_path_in + file_name)

    logger.info("create_SQC_file : " + str(file_path_in + file_name) + ', creat time ' + str(time.time() - start))
    # print('create_file time = ', time.time() - start)
    logger.info("finish do create_SQC_file ...")
    return (file_path_in + file_name)


from os import walk
from os.path import join
import shutil
from dask import dataframe as dd


def process_SQC2JUDGE_file(file_path_in=SQC_IN['file_path_in'], file_path_orgin=SQC_IN['file_path_orgin'],
                           file_path_judge=SQC_IN['file_path_judge'], file_path_qcout=SQC_IN['file_path_qcout']):
    logger.info("start do process_SQC2JUDGE_file ...")
    in_file_list = []
    for root, dirs, files in walk(file_path_in):
        for f in files:
            in_file_list.append(join(root, f))
    # print(file_path_in, ' in_file_list = ', in_file_list)
    logger.info("search SQC_file list : " + str(in_file_list))

    for in_file in in_file_list:
        try:
            start = time.time()
            # print("in_file = ", in_file)
            logger.info("search SQC_file name : " + in_file)
            ck_file = in_file.split('/')[-1]
            wafer_id = ck_file.split('#')[0] + "#" + ck_file.split('#')[1] + "#" + ck_file.split('#')[2]
            wafer_area = ck_file.split('#')[-4]
            chip_x, chip_y = int(ck_file.split('#')[-3]), int(ck_file.split('#')[-2])
            chip_layout = '{0:04d}'.format(chip_x) + '#' + '{0:04d}'.format(chip_y)
            start1 = time.time()
            dask_df = dd.read_csv(in_file)
            # print('read_file time = ', time.time() - start1)
            logger.info("search SQC_file : " + in_file + ", read time = " + str(time.time() - start1))
            column_chip_x = ['x' + '{0:04d}'.format(i + 1) for i in range(chip_x)]
            ck = 0
            for ins_item in ins_dir.keys():
                # start2 = time.time()
                file_name = wafer_id + '#' + wafer_area + '#' + chip_layout + '#' + ins_item + '_orgin_v000.csv'
                df_ins = pd.DataFrame(data=np.array(dask_df.loc[:, [ins_item]]).reshape([chip_y, chip_x]),
                                      columns=column_chip_x)
                df_ins.to_csv(file_path_orgin + file_name)
                b1 = np.array(
                    [number < ins_dir[ins_item]['min_set'] for number in np.array(dask_df.loc[:, [ins_item]])])
                b2 = np.array(
                    [number > ins_dir[ins_item]['max_set'] for number in np.array(dask_df.loc[:, [ins_item]])])
                b3 = np.concatenate((b1, b2), axis=1)
                set_axis = 1
                index_array = np.argmax(b3, axis=set_axis)
                b3 = np.take_along_axis(b3, np.expand_dims(index_array, axis=set_axis), axis=set_axis)
                df_jug = pd.DataFrame(data=1 * b3.reshape([chip_y, chip_x]), columns=column_chip_x)
                file_name = wafer_id + '#' + wafer_area + '#' + chip_layout + '#' + ins_item + '_judge_v000.csv'
                df_jug.to_csv(file_path_judge + file_name)
                # print('write_2*judge_file time = ', time.time() - start2)
                if ck == 0:
                    b4 = np.concatenate((b1, b2), axis=1)
                    ck += 1
                else:
                    b4 = np.concatenate((b4, b1, b2), axis=1)
            shutil.move(in_file,
                        in_file[
                        :-1 * (len(in_file.split('/')[-1]) + 1 + len(in_file.split('/')[-2]))] + '0_SQC_HISTORY/' +
                        in_file.split('/')[-1])
            logger.info("search SQC_file : " + in_file + ", move to " + str(
                in_file[:-1 * (len(in_file.split('/')[-1]) + 1 + len(in_file.split('/')[-2]))]) + '0_SQC_HISTORY/' +
                        in_file.split('/')[-1])
            # print('judge_file time = ', time.time() - start)
            logger.info("search SQC_file : " + in_file + ", process judge file time = " + str(time.time() - start))

            set_axis = 1
            index_array = np.argmax(b4, axis=set_axis)
            b4 = np.take_along_axis(b4, np.expand_dims(index_array, axis=set_axis), axis=set_axis)
            df_jug = pd.DataFrame(data=1 * b4.reshape([chip_y, chip_x]), columns=column_chip_x)
            file_name = wafer_id + '#' + wafer_area + '#OX_' + time.strftime("%Y%m%d%H%M%S") + '_v000.csv'
            df_jug.to_csv(file_path_qcout + file_name)
            # print('create_OX_file time = ', time.time() - start)
            logger.info("search SQC_file : " + in_file + ", process judge OX time = " + str(time.time() - start))

        except:
            print("file_error")
            logger.info("search SQC_file : " + in_file + ", error to process judge file")
            shutil.move(in_file,
                        in_file[
                        :-1 * (len(in_file.split('/')[-1]) + 1 + len(in_file.split('/')[-2]))] + '0_SQC_HISTORY/' +
                        'NG_' + in_file.split('/')[-1])
            logger.info("error search SQC_file : " + in_file + ", move to " + str(in_file[:-1 * (
                        len(in_file.split('/')[-1]) + 1 + len(in_file.split('/')[-2]))]) + '0_SQC_HISTORY/' + 'NG_' +
                        in_file.split('/')[-1])
    logger.info("finish do process_SQC2JUDGE_file ...")


from dask import dataframe as dd
import os.path, time
import glob


def update_USE2JUDGE_file(search_wafer='LON20210920190918', file_path_used=SQC_IN['file_path_used'],
                          file_path_orgin=SQC_IN['file_path_orgin'], file_path_judge=SQC_IN['file_path_judge'],
                          file_path_qcout=SQC_IN['file_path_qcout']):
    logger.info("start do update_USE2JUDGE_file ...")
    start = time.time()
    search_wafer = '*' + search_wafer + '*'
    search_orgin_file = glob.glob(file_path_orgin + search_wafer)
    search_used_file = glob.glob(file_path_used + search_wafer)
    # print('search_used_cnt = ', len(search_used_file))
    # print('search_orgin_cnt = ', len(search_orgin_file))
    logger.info("search used_file cnt : " + str(len(search_used_file)))
    logger.info("search used_file`s orgin_file cnt : " + str(len(search_orgin_file)))
    used_ck = 0
    for in_file in search_used_file:
        read_df = pd.read_csv(in_file)
        if used_ck == 0:
            used_df = read_df
            used_ck += 1
        else:
            used_df = pd.concat((used_df, read_df), axis=0)
    if used_ck > 0:
        used_df = used_df.sort_values(by=['x_index_start', 'y_index_start', 'x_index_end', 'y_index_end'],
                                      ascending=[True, True, True, True]).reset_index(drop=True)
        r_counter, c_counter = used_df.shape
        used_df['x_index_start'] = used_df['x_index_start'] - 1
        used_df['y_index_start'] = used_df['y_index_start'] - 1
    else:
        used_df = []
        r_counter, c_counter = 0, 0
    ck = 0
    for in_file in search_orgin_file:
        # print('in_file= ', in_file)
        # print('file_update_time = ', time.ctime(os.path.getmtime(in_file)))
        # print('file_create_time = ', time.ctime(os.path.getctime(in_file)))
        try:
            ck_file = in_file.split('\\')[-1]
            wafer_id = ck_file.split('#')[0] + "#" + ck_file.split('#')[1] + "#" + ck_file.split('#')[2]
            wafer_area = ck_file.split('#')[-4]
            chip_x, chip_y = int(ck_file.split('#')[-3]), int(ck_file.split('#')[-2])
            chip_layout = '{0:04d}'.format(chip_x) + '#' + '{0:04d}'.format(chip_y)
            file_version = int(ck_file.split('#')[-1][-7:-4]) + 1
            ins_item = ck_file.split('#')[-1].split('_')[0] + '_' + ck_file.split('#')[-1].split('_')[1]
            out_file = in_file[:-7] + '{0:03d}'.format(file_version) + in_file[-4:]
            start1 = time.time()
            dask_df = dd.read_csv(in_file)
            # print('read_file time = ', time.time() - start1)
            logger.info("search used_file`s orgin_file : " + in_file + ", process read_orgin_file time = " + str(
                time.time() - start1))

            column_chip_x = ['x' + '{0:04d}'.format(i + 1) for i in range(chip_x)]
            start2 = time.time()
            pandas_df = dask_df.compute()[column_chip_x].reset_index(drop=True)
            for i in range(r_counter):
                pandas_df.iloc[used_df['y_index_start'][i]:used_df['y_index_end'][i]:used_df['y_index_step'][i],
                used_df['x_index_start'][i]:used_df['x_index_end'][i]:used_df['x_index_step'][i]] = 999999
            pandas_df.to_csv(out_file)
            b1 = (pandas_df < ins_dir[ins_item]['min_set']).values.reshape(pandas_df.shape[0], pandas_df.shape[1], -1)
            b2 = (pandas_df > ins_dir[ins_item]['max_set']).values.reshape(pandas_df.shape[0], pandas_df.shape[1], -1)
            b3 = np.concatenate((b1, b2), axis=2)
            set_axis = 2
            index_array = np.argmax(b3, axis=set_axis)
            b3 = np.take_along_axis(b3, np.expand_dims(index_array, axis=set_axis), axis=set_axis)
            df_jug = pd.DataFrame(data=1 * b3.reshape([chip_y, chip_x]), columns=column_chip_x)
            file_name = ck_file[:-15] + '_judge_v000' + ck_file[-4:]
            df_jug.to_csv(file_path_judge + file_name)
            # print('write_orgin+judge_file time = ', time.time() - start2)
            logger.info("search used_file`s orgin_file : " + in_file + ", process write_orgin+judge_file time = " + str(
                time.time() - start2))

            if ck == 0:
                b4 = np.concatenate((b1, b2), axis=2)
                ck += 1
            else:
                b4 = np.concatenate((b4, b1, b2), axis=2)
            set_axis = 2
            index_array = np.argmax(b4, axis=set_axis)
            b4 = np.take_along_axis(b4, np.expand_dims(index_array, axis=set_axis), axis=set_axis)
            df_jug = pd.DataFrame(data=1 * b4.reshape([chip_y, chip_x]), columns=column_chip_x)
            file_name = wafer_id + '#' + wafer_area + '#OX_' + time.strftime("%Y%m%d%H%M%S") + '_v000.csv'
            df_jug.to_csv(file_path_qcout + file_name)
            # print('update_file time = ', time.time() - start)
            logger.info(
                "search used_file`s orgin_file : " + in_file + ", process judge OX time = " + str(time.time() - start))
            shutil.move(in_file,
                        in_file.split('\\')[0][
                        :-1 * len(in_file.split('\\')[0].split('/')[-1])] + '/2_QC_JUDGE_HISTORY/' +
                        ck_file)
            logger.info("search used_file`s orgin_file : " + in_file + ", move to " + str(in_file.split('\\')[0][
                                                                                          :-1 * len(in_file.split('\\')[
                                                                                                        0].split('/')[
                                                                                                        -1])]) + '2_QC_JUDGE_HISTORY/' + ck_file)
        except:
            # print("file_error")
            logger.info("search used_file`s orgin_file : " + in_file + ", error to process update_USE2JUDGE_file")
            shutil.move(in_file,
                        in_file.split('\\')[0][
                        :-1 * len(in_file.split('\\')[0].split('/')[-1])] + '2_QC_JUDGE_HISTORY/' +
                        'NG_' + ck_file)
            logger.info("error search used_file`s orgin_file : " + in_file + ", move to " + str(in_file.split('\\')[0][
                                                                                                :-1 * len(
                                                                                                    in_file.split('\\')[
                                                                                                        0].split('/')[
                                                                                                        -1])]) + '2_QC_JUDGE_HISTORY/' + 'NG_' + ck_file)

    if used_ck > 0:
        for in_file in search_used_file:
            ck_file = in_file.split('\\')[-1]
            shutil.move(in_file,
                        in_file.split('\\')[0][:-1 * len(in_file.split('\\')[0].split('/')[-1])] + '1_USE_HISTORY/' +
                        ck_file)
            logger.info("search used_file : " + in_file + ", move to " + str(
                in_file.split('\\')[0][:-1 * len(in_file.split('\\')[0].split('/')[-1])]) + '1_USE_HISTORY/' + ck_file)
    logger.info("finish do update_USE2JUDGE_file ...")


def process_USE2JUDGE_file(file_path_used=SQC_IN['file_path_used']):
    logger.info("start do process_USE2JUDGE_file ...")
    search_used_file = glob.glob(file_path_used + '*')
    # print('search_used_file = ', len(search_used_file))
    logger.info("search used_file cnt : " + str(len(search_used_file)))
    search_used_list = []
    for root, dirs, files in walk(file_path_used):
        for f in files:
            search_used_list.append([f.split('#')[2]])
    search_wafer_list = np.unique(search_used_list)
    for wafer in search_wafer_list:
        # print('search_wafer = ', wafer)
        logger.info("search used_file`s wafer : " + wafer)
        update_USE2JUDGE_file(search_wafer=wafer)
    logger.info("finish do process_USE2JUDGE_file ...")


def update_JUDGE2AREA_file(wafer_id='LON20210920190918', file_path_orgin=SQC_IN['file_path_orgin'],
                           file_path_qcout=SQC_IN['file_path_qcout'],
                           file_path_area_orgin=SQC_IN['file_path_area_orgin'],
                           file_path_area_judge=SQC_IN['file_path_area_judge']):
    logger.info("start do update_USE2AREA_file ...")
    f = lambda x: 1 if x < 2 else x

    start = time.time()
    search_wafer = '*' + wafer_id + '*'
    search_orgin_file = glob.glob(file_path_orgin + search_wafer)
    search_OX_file = glob.glob(file_path_qcout + search_wafer)
    # print('search_OX_cnt = ', len(search_OX_file))
    # print('search_orgin_cnt = ', len(search_orgin_file))
    logger.info("search OX_file cnt : " + str(len(search_OX_file)))
    logger.info("search OX_file`s orgin_file cnt : " + str(len(search_orgin_file)))

    if len(search_OX_file) > 0 and len(search_orgin_file) > 0:
        ox_ck = 0
        ox_file_list = []
        for in_file in search_OX_file:
            ck_file = in_file.split('\\')[-1]
            # print(in_file)
            ox_file_list.append([wafer_id, ck_file.split('#')[-1].split('_')[1], in_file])
        if len(ox_file_list) > 0:
            df_ox = pd.DataFrame(data=np.array(ox_file_list),
                                 columns=['wafer_id', 'process_time', 'file_path']).groupby(
                'wafer_id').max().reset_index()
            # print('df_ox = ', df_ox[['wafer_id', 'process_time']])
            logger.info('df_ox = ' + str(df_ox[['wafer_id', 'process_time']]))

        else:
            df_ox = []
            print('df_ox = []')
            logger.info('df_ox = []')
        position_xy = []
        ck = 0
        ins_list = []
        for ox_index in range(len(df_ox)):
            ck_file = df_ox['file_path'].iloc[ox_index].split('\\')[-1]

            file_path_orgin = SQC_IN['file_path_orgin']
            search_orgin_file = glob.glob(file_path_orgin + search_wafer)

            pandas_df = pd.read_csv(df_ox['file_path'].iloc[ox_index], index_col=0)
            chip_y, chip_x = pandas_df.shape
            # print('file_path = ', df_ox['file_path'].iloc[ox_index])
            # print(df_ox['wafer_id'].iloc[ox_index], 'chip_x, chip_y, len_search_orgin_file = ', chip_x, chip_y, len(search_orgin_file))
            # print('chip_x, pixel_x, area_x, chip_y, pixel_y, area_y, less_ng_cnt = ', chip_x, pixel_repeat_x, area_repeat_x, chip_y, pixel_repeat_y, area_repeat_y, less_ng_cnt)
            logger.info('file_path = ' + str(df_ox['file_path'].iloc[ox_index]))
            logger.info(
                str(df_ox['wafer_id'].iloc[ox_index]) + 'chip_x, chip_y, len_search_orgin_file = ' + str(chip_x) + str(
                    chip_y) + str(len(search_orgin_file)))
            logger.info('chip_x, pixel_x, area_x, chip_y, pixel_y, area_y, less_ng_cnt = ' + str(chip_x) + str(
                pixel_repeat_x) + str(area_repeat_x) + str(chip_y) + str(pixel_repeat_y) + str(area_repeat_y) + str(
                less_ng_cnt))
            block_x = int(chip_x / (pixel_repeat_x * area_repeat_x))
            block_y = int(chip_y / (pixel_repeat_y * area_repeat_y))
            position_x = chip_x - (pixel_repeat_x * (area_repeat_x - 1))
            position_y = chip_y - (pixel_repeat_y * (area_repeat_y - 1))

            if (chip_x <= (pixel_repeat_x * (area_repeat_x - 1))) or (chip_y <= (pixel_repeat_y * (area_repeat_y - 1))):
                # print("chip not enough to setting block")
                logger.info("chip not enough to setting block")
            else:
                position_x = chip_x - (pixel_repeat_x * (area_repeat_x - 1))
                position_y = chip_y - (pixel_repeat_y * (area_repeat_y - 1))
                for select_y_position in range(position_y):
                    for select_x_position in range(position_x):
                        select_position_sx, select_position_sy = select_x_position + 1, select_y_position + 1
                        select_position_ex, select_position_ey = select_x_position + pixel_repeat_x * (
                                area_repeat_x - 1) + 1, select_y_position + pixel_repeat_y * (area_repeat_y - 1) + 1
                        select_position_bx, select_position_by = int(select_x_position / pixel_repeat_x), int(
                            select_y_position / pixel_repeat_y)
                        select_position_px, select_position_py = int(select_x_position % pixel_repeat_x), int(
                            select_y_position % pixel_repeat_y)
                        ng_cnt = pandas_df.iloc[
                                 select_y_position:select_y_position + pixel_repeat_y * area_repeat_y:pixel_repeat_y,
                                 select_x_position:select_x_position + pixel_repeat_x * area_repeat_x:pixel_repeat_x].to_numpy().sum()
                        position_xy.append(
                            [len(search_orgin_file), df_ox['wafer_id'].iloc[ox_index], select_position_bx,
                             select_position_by, select_position_px, select_position_py, select_position_sx,
                             select_position_sy, select_position_ex, select_position_ey, ng_cnt])

                        for in_file in search_orgin_file:
                            ck_file = in_file.split('\\')[-1]
                            ins_item = ck_file.split('#')[-1].split('_')[0] + '_' + ck_file.split('#')[-1].split('_')[1]
                            ins_df = pd.read_csv(in_file, index_col=0)
                            ins_df[ins_df == 999999] = np.nan
                            ins_sum = ins_df.iloc[
                                      select_y_position:select_y_position + pixel_repeat_y * area_repeat_y:pixel_repeat_y,
                                      select_x_position:select_x_position + pixel_repeat_x * area_repeat_x:pixel_repeat_x].sum(
                                skipna=True).sum(skipna=True)
                            ins_min = ins_df.iloc[
                                      select_y_position:select_y_position + pixel_repeat_y * area_repeat_y:pixel_repeat_y,
                                      select_x_position:select_x_position + pixel_repeat_x * area_repeat_x:pixel_repeat_x].min(
                                skipna=True).min(skipna=True)
                            ins_mean = ins_df.iloc[
                                       select_y_position:select_y_position + pixel_repeat_y * area_repeat_y:pixel_repeat_y,
                                       select_x_position:select_x_position + pixel_repeat_x * area_repeat_x:pixel_repeat_x].mean(
                                skipna=True).mean(skipna=True)
                            ins_max = ins_df.iloc[
                                      select_y_position:select_y_position + pixel_repeat_y * area_repeat_y:pixel_repeat_y,
                                      select_x_position:select_x_position + pixel_repeat_x * area_repeat_x:pixel_repeat_x].max(
                                skipna=True).max(skipna=True)
                            ins_std = ins_df.iloc[
                                      select_y_position:select_y_position + pixel_repeat_y * area_repeat_y:pixel_repeat_y,
                                      select_x_position:select_x_position + pixel_repeat_x * area_repeat_x:pixel_repeat_x].std(
                                skipna=True).std(skipna=True)
                            ins_spc_name = ['0sum', '1min', '2mean', '3max', '4std']
                            ins_spc_value = [ins_sum, ins_min, ins_mean, ins_max, ins_std]
                            for spc_index in range(len(ins_spc_name)):
                                # print(ins_item + '_' + ins_spc_name[spc_index], ' = ', ins_spc_value[spc_index])
                                ins_list.append(
                                    [df_ox['wafer_id'].iloc[ox_index], select_position_bx, select_position_by,
                                     select_position_px, select_position_py, select_position_sx, select_position_sy,
                                     select_position_ex, select_position_ey, ng_cnt,
                                     ins_item + '_' + ins_spc_name[spc_index], ins_spc_value[spc_index]])

        df_ins = pd.DataFrame(data=np.array(ins_list),
                              columns=['wafer_id', 'bx', 'by', 'px', 'py', 'sx', 'sy', 'ex', 'ey', 'ng_cnt', 'ins_name',
                                       'ins_value']).sort_values(by=['wafer_id', 'bx', 'by', 'px', 'py'],
                                                                 ascending=[True, True, True, True, True]).reset_index(
            drop=True)
        ins_r2c = df_ins.pivot_table('ins_value',
                                     index=['wafer_id', 'bx', 'by', 'px', 'py', 'sx', 'sy', 'ex', 'ey', 'ng_cnt'],
                                     columns='ins_name', aggfunc='mean')
        ins_r2c = ins_r2c.reset_index()
        file_name = ck_file.split('#')[0] + "#" + ck_file.split('#')[1] + "#" + ck_file.split('#')[
            2] + '#AREA_ORGIN_' + time.strftime("%Y%m%d%H%M%S") + '_v000.csv'
        ins_r2c.to_csv(file_path_area_orgin + file_name)
        # print('update_file time = ', time.time() - start)
        logger.info("update_USE2AREA_file : " + wafer_id + ", process area orgin time = " + str(time.time() - start))



    else:
        # print("error search wafer : ", + search_wafer + " loss OX_file or orgin_file " + str(len(search_OX_file)) + ', ' + str(len(search_orgin_file)))
        logger.info("error search wafer : " + search_wafer + " loss OX_file or orgin_file " + str(
            len(search_OX_file)) + ', ' + str(len(search_orgin_file)))
    logger.info("finish do update_USE2AREA_file ...")


def process_JUDGE2AREA_file(file_path_qcout=SQC_IN['file_path_qcout']):
    logger.info("start do process_JUDGE2AREA_file ...")
    search_OX_file = glob.glob(file_path_qcout + '*')
    # print('search_qcout_file = ', len(search_OX_file))
    logger.info("search qcout_file cnt : " + str(len(search_OX_file)))
    search_OX_list = []
    for root, dirs, files in walk(file_path_qcout):
        for f in files:
            search_OX_list.append([f.split('#')[2]])
    search_wafer_list = np.unique(search_OX_list)
    for wafer in search_wafer_list:
        # print('search_wafer = ', wafer)
        logger.info("search used_file`s wafer : " + wafer)
        update_JUDGE2AREA_file(wafer_id=wafer)
    logger.info("finish do process_JUDGE2AREA_file ...")

