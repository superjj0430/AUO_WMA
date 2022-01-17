from django.shortcuts import render
from .models import *
from app.serializer import Serializer
from rest_framework.decorators import api_view
import json
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import numpy as np
import time
import os 
import shutil
from datetime import datetime
from django.http import HttpResponse, StreamingHttpResponse

from WMA_V3 import WMA
import math

# base on FBV
# Multi-condition search
@api_view(['POST'])
def mcs(request):

    # handel json decode error
    # input json格式檢查
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)

    # handle schema format error
    request_data_check = json_validation(request_data)
    if request_data_check == "True":
        # print(request_data)
        data = mcs_func(request_data.get('SUPPLIER_NAME'), request_data.get('SUPPLIER_TYPE'), request_data.get('WAFER_ID'), request_data.get('WAFER_SIZE'), request_data.get('LED_SPEC_WD_AVG'), request_data.get('LED_SPEC_WD_MIN'), request_data.get('LED_SPEC_WD_MAX'))
        # print(data)
        serializer = Serializer(data, many=True)
        print(type(data))
        return Response(serializer.data)
        

    return Response(request_data_check, status=status.HTTP_400_BAD_REQUEST)


# 取得全部material list
@api_view(['GET'])
def get_material_list(request):
    data = pd.read_csv(r'./Data_Archived/wafer_list.csv')
    material_list = []  
    try:
        for i in range(data.shape[0]):
            material_content_dict = {}
            material_content_dict['WAFER_ID'] = data['WAFER_ID'][i] if not isinstance(data['WAFER_ID'][i], float) else None
            material_content_dict['CARRIER_TYPE'] = data['CARRIER_TYPE'][i] if not isinstance(data['CARRIER_TYPE'][i], float) else None
            material_content_dict['WAFER_SIZE'] = data['WAFER_SIZE'][i] if not math.isnan(data['WAFER_SIZE'][i]) else None 
            material_content_dict['LED_TYPE'] = data['LED_TYPE'][i] if not isinstance(data['LED_TYPE'][i], float) else None
            material_content_dict['AREA_CNT'] = data['AREA_CNT'][i] if not math.isnan(data['AREA_CNT'][i]) else None 
            material_content_dict['CHIP_X_CNT'] = data['CHIP_X_CNT'][i] if not math.isnan(data['CHIP_X_CNT'][i]) else None 
            material_content_dict['CHIP_Y_CNT'] = data['CHIP_Y_CNT'][i] if not math.isnan(data['CHIP_Y_CNT'][i]) else None 
            material_content_dict['LED_PITCH_X'] = data['LED_PITCH_X'][i] if not math.isnan(data['LED_PITCH_X'][i]) else None 
            material_content_dict['LED_PITCH_Y'] = data['LED_PITCH_Y'][i] if not math.isnan(data['LED_PITCH_Y'][i]) else None 
            material_content_dict['STATUS'] = data['STATUS'][i] if not isinstance(data['STATUS'][i], float) else None 
            material_content_dict['MODEL_NO'] = data['MODEL_NO'][i] if not isinstance(data['MODEL_NO'][i], float) else None
            material_content_dict['JUDGE_SPEC_ID'] = data['JUDGE_SPEC_ID'][i] if not isinstance(data['JUDGE_SPEC_ID'][i], float) else None
            material_content_dict['LED_NG_CNT'] = data['LED_NG_CNT'][i] if not math.isnan(data['LED_NG_CNT'][i]) else None
            material_content_dict['LED_USED_CNT'] = data['LED_USED_CNT'][i] if not math.isnan(data['LED_USED_CNT'][i]) else None
            material_content_dict['AREA_OK_CNT'] = data['AREA_OK_CNT'][i] if not math.isnan(data['AREA_OK_CNT'][i]) else None
            material_content_dict['AREA_USED_CNT'] = data['AREA_USED_CNT'][i] if not math.isnan(data['AREA_USED_CNT'][i]) else None
            material_content_dict['HEATMAP_URL'] = data['HEATMAP_URL'][i] if not isinstance(data['HEATMAP_URL'][i], float) else None
            material_content_dict['QC_DOWNLOAD'] = data['QC_DOWNLOAD'][i] if not isinstance(data['QC_DOWNLOAD'][i], float) else None
            material_content_dict['OUTPUT_PATH'] = data['OUTPUT_PATH'][i] if not isinstance(data['OUTPUT_PATH'][i], float) else None
            material_content_dict['LED_SIZE_X'] = data['LED_SIZE_X'][i] if not math.isnan(data['LED_SIZE_X'][i]) else None
            material_content_dict['LED_SIZE_Y'] = data['LED_SIZE_Y'][i] if not math.isnan(data['LED_SIZE_Y'][i]) else None
            material_list.append(material_content_dict)
        return Response(list(material_list), status=status.HTTP_200_OK)

    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

# 取得area list，分成全部與by model no
@api_view(['POST'])
def get_wafer_area_list(request):
    wafer_area_list = pd.read_csv(r'./Data_Archived/wafer_area_list.csv')
    wafer_area_list = wafer_area_list.fillna('')
    try:
        request_data = json.loads(request.body)
        print(type(request_data))

    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)    

    try:
        if request_data["MODEL_NO"] == "ALL":
            
            content_list = []
            for i in list(set(wafer_area_list["wafer_id"])):
                content_dict = {}
                content_dict["wafer_id"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["wafer_id"])[0]
                content_dict["area_sno"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["area_sno"])[0]
                content_dict["area_scnt"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["area_scnt"])[0]
                content_dict["crx"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["crx"])[0]
                content_dict["cry"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["cry"])[0]
                content_dict["arx"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["arx"])[0]
                content_dict["ary"] = list(wafer_area_list[wafer_area_list["wafer_id"] == i]["area_scnt"])[0]
                tmp = wafer_area_list[wafer_area_list["wafer_id"] == i]
                tmp = tmp.drop(['wafer_id', 'area_sno', 'area_scnt', 'crx', 'cry', 'arx', 'ary'], axis=1)
                content_dict["area_info"] = tmp.to_dict(orient='records')
                content_list.append(content_dict)
            return Response(content_list, status=status.HTTP_200_OK)
        else:
            wafer_area_list = wafer_area_list[wafer_area_list["MODEL_NO"].str.contains(request_data["MODEL_NO"])]
            print(wafer_area_list.info())
            return Response(list(wafer_area_list.to_dict(orient='records')), status=status.HTTP_200_OK)
            
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 取得spec list
@api_view(['GET'])
def get_spec_list(request):
    data = pd.read_csv(r'./Data_Archived/model_spec.csv')
    temp = pd.DataFrame()
    new_ver_dict = {}
    SPEC_list = []
    try:
        # 找出各modle最新版本
        for i in range(data.shape[0]):
            if data['MODEL_NO'][i] in new_ver_dict.keys() and (int(data['SPEC_VER'][i][1:]) <= int(new_ver_dict[data['MODEL_NO'][i]][1:])):
                print(data['MODEL_NO'][i])
                continue
            else:
                new_ver_dict[data['MODEL_NO'][i]] = data['SPEC_VER'][i]
        # {'V126FLN01': 'V2', 'V130FLN02': 'V1'}
        print(new_ver_dict)
    
        for item in list(new_ver_dict.keys()):
            spec_content_dict = {}
            ins_type_list = []
            temp = data[data['MODEL_NO'].str.contains(item) & data['SPEC_VER'].str.contains(new_ver_dict[item])]
            inst_type = list(set(temp['INS_TYPE']))
            spec_content_dict['MODEL_NO'] = list(temp['MODEL_NO'])[0]
            spec_content_dict['JUDGE_SPEC_ID'] = list(temp['JUDGE_SPEC_ID'])[0]
            # spec_content_dict['LED_TYPE'] = list(temp['LED_TYPE'])[0]
            spec_content_dict['PIXEL_REPEAT_X'] = list(temp['PIXEL_REPEAT_X'])[0]
            spec_content_dict['PIXEL_REPEAT_Y'] = list(temp['PIXEL_REPEAT_Y'])[0]
            spec_content_dict['AREA_REPEAT_X'] = list(temp['AREA_REPEAT_X'])[0]
            spec_content_dict['AREA_REPEAT_Y'] = list(temp['AREA_REPEAT_Y'])[0]
            spec_content_dict['AREA_LESS_NG'] = list(temp['AREA_LESS_NG'])[0]
            spec_content_dict['GRADE_NAME'] = list(temp['GRADE_NAME'])[0]
            spec_content_dict['SPEC_VER'] = list(temp['SPEC_VER'])[0]
            spec_content_dict['SPEC_DATE'] = list(temp['SPEC_DATE'])[0]

            for type in inst_type:
                max_min_dict = {}
                max_min_dict['INS_TYPE'] = type
                max_min_dict['SPEC_MAX'] = list(temp[temp['INS_TYPE'].str.contains(type)]['SPEC_MAX'])[0]
                max_min_dict['SPEC_MIN'] = list(temp[temp['INS_TYPE'].str.contains(type)]['SPEC_MIN'])[0]
                ins_type_list.append(max_min_dict)
            spec_content_dict['SPEC'] = ins_type_list
            SPEC_list.append(spec_content_dict)
        return Response(list(SPEC_list), status=status.HTTP_200_OK)
    
    except Exception as e:
        print(e)
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 於spec list上增加spec
@api_view(['POST'])
def add_spec(request):
    spec_file_path = './Data_Archived/model_spec.csv'
    spec_file = pd.read_csv(spec_file_path)
    # handel json decode error
    try:
        request_data = json.loads(request.body)
        print(type(request_data))

    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)


    # handle schema format error
    request_data_check = spec_json_validation(request_data)
    exist_check = check_exits(spec_file_path, request_data) 
    print("request_data_check: ", request_data_check)
    if request_data_check  and exist_check:
        try:
            # generate 7 rows accroding to the INS_TYPE
            for i in request_data['SPEC']:
                spec_file = spec_file.append({'MODEL_NO': request_data['MODEL_NO'],
                'JUDGE_SPEC_ID': request_data['JUDGE_SPEC_ID'],
                'PIXEL_REPEAT_X': request_data['PIXEL_REPEAT_X'], 'PIXEL_REPEAT_Y': request_data['PIXEL_REPEAT_Y'],
                'AREA_REPEAT_X': request_data['AREA_REPEAT_X'], 'AREA_REPEAT_Y': request_data['AREA_REPEAT_Y'],
                'AREA_LESS_NG': request_data['AREA_LESS_NG'],  'GRADE_NAME': request_data['GRADE_NAME'],
                'INS_TYPE': i['INS_TYPE'], 'SPEC_MIN': i['SPEC_MIN'], 'SPEC_MAX': i['SPEC_MAX'],
                'SPEC_VER': 'V1', 'SPEC_DATE': time.strftime('%Y/%m/%d %H:%M', time.localtime())
                }, ignore_index=True)
            spec_file.to_csv('./Data_Archived/model_spec.csv', mode='w', index=False)
            return Response("Add SPEC success!", status=status.HTTP_200_OK)

        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
    return Response("Json Format Wrong!" if not request_data_check else "SPEC Exist!", status=status.HTTP_400_BAD_REQUEST)


# 檢查輸入的spec是否存在於spec list
def check_exits(spec_file_path, request_data):
    spec_file = pd.read_csv(spec_file_path)
    if request_data.get("MODEL_NO") in list(dict.fromkeys(list(spec_file["MODEL_NO"]))):
        return False
    return True


# 確認輸入的wafer id是否已存在wafer list中
@api_view(['POST'])
def id_exist_check(request):
    # handel json decode error
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)

    wafer_list = pd.read_csv(r'./Data_Archived/wafer_list.csv')

    try:
        if request_data["ID"] in wafer_list['WAFER_ID'].tolist():
            return Response(True, status=status.HTTP_200_OK)
        else:
            return Response(False, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)


# 用於解析sqc in資料part a資訊(1)
@api_view(['POST'])
def get_parta_info(request):
    # handel json decode error
    get_parta_info_list = []
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)

    try:
        # judge input id and file id
        parta_info = parse_partA(request_data["FILE_PATH"])
        print(parta_info)
        get_parta_info_list.append(parta_info)
        return Response(list(get_parta_info_list), status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

# 用於解析sqc in資料part a資訊(2)
def parse_partA(file_path):
    sqc_file = pd.read_csv(file_path, nrows=25, skiprows=1, usecols=[0,1], names = ['name', 'value'])
    parta_info = pd.Series(sqc_file.value.values, index=sqc_file.name).to_dict()
    parta_info['LED_TYPE'] = parta_info['LED_TYPE'][1:-1]
    parta_info['WAFER_ID'] = parta_info['WAFER_ID'][1:-1]
    parta_info['SUPPLIER_DATE'] = parta_info['SUPPLIER_DATE'][1:-1]
    parta_info['CHIP_X_CNT'] = parta_info['LED_CNT_X']
    parta_info['CHIP_Y_CNT'] = parta_info['LED_CNT_Y']
    parta_info['CARRIER_TYPE'] = parta_info['SUPPLIER_TYPE']
    parta_info['AREA_CNT'] = parta_info['LED_SHOT_SUM']

    return parta_info


# 用於 final qc in confirm
# 判斷part b與part a資訊是否一至 -> 更新qc資料至wafer list -> 更新計算用設定json檔案 -> 執行WMA QCTOJUDGE -> 執行WMA JUDGE2AREA -> 執行WMA AREA2JUDGE -> 結束
@api_view(['POST'])
def qcin_confirm__2(request):
    # handel json decode error
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)
    
    parta_info = parse_partA(request_data["FILE_PATH"])
    if parse_partB(parta_info, request_data["FILE_PATH"])[0]:
        try:
            sqc2waferlist(parta_info, request_data["MODEL_NO"])
            update_wma_json(parta_info, request_data["MODEL_NO"])
            WMA.setup_file()
            WMA.process_SQC2JUDGE_file()
            WMA.update_JUDGE2AREA_file(parta_info['WAFER_ID'])
            WMA.create_AREA2JUDGE_file(parta_info['WAFER_ID'], less_ng_cnt=49500)
            os.remove(request_data["FILE_PATH"])
            return Response(True, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(parse_partB(parta_info, request_data["FILE_PATH"]), status=status.HTTP_200_OK)

# 更新qc資料至wafer list
def sqc2waferlist(parta_info, MODEL_NO):
    wafer_list = pd.read_csv(r'./Data_Archived/wafer_list.csv')
    try:
        wafer_list = wafer_list.append({
            'CARRIER_TYPE': parta_info['CARRIER_TYPE'],
            'WAFER_ID': parta_info['WAFER_ID'],
            'WAFER_SIZE': parta_info['WAFER_SIZE'],
            'LED_TYPE': parta_info['LED_TYPE'],
            'AREA_CNT': parta_info['AREA_CNT'],
            'CHIP_X_CNT': parta_info['CHIP_X_CNT'],
            'CHIP_Y_CNT': parta_info['CHIP_Y_CNT'],
            'LED_PITCH_X': parta_info['LED_PITCH_X'],
            'LED_PITCH_Y': parta_info['LED_PITCH_Y'],
            'LED_SIZE_X': parta_info['LED_SIZE_X'],
            'LED_SIZE_Y': parta_info['LED_SIZE_Y'],
            'STATUS': "JUDGED",
            'MODEL_NO': MODEL_NO,
            'JUDGE_SPEC_ID': None,
            'LED_NG_CNT': None,
            'LED_NG_CNT': None,
            'LED_USED_CNT': None,
            'AREA_OK_CNT': None,
        }, ignore_index = True)

        wafer_list.to_csv('./Data_Archived/wafer_list.csv', mode='w', index =False)
        print('wafer_list update success!')
    except Exception as e:
        print(e)

# 判斷part b與part a資訊是否一至
def parse_partB(parta_info, file_path):
    print('parse_partB')
    # print(file_path)
    sqc_file = pd.read_csv(file_path, skiprows=28)
    sqc_file = sqc_file.dropna(subset=['COORDINATE_X', 'COORDINATE_Y'])

    file_path_in = r"./WMA_V3/data/0_SQC_IN/"
    chip_x = list(set(sqc_file['COORDINATE_X']))
    chip_y = list(set(sqc_file['COORDINATE_Y']))
    ins_cnt = len(sqc_file.columns.tolist())
    start = time.time()

    print('chip_x_cnt: ', len(chip_x), 'chip_y_cnt: ', len(chip_y))
    print('int(parta_info["CHIP_X_CNT"])): ', int(parta_info["CHIP_X_CNT"]), 'int(parta_info["CHIP_Y_CNT"])): ', int(parta_info["CHIP_Y_CNT"]))


    # parta&b XY種類confirm
    if (len(chip_x) != int(parta_info["CHIP_X_CNT"])) or len(chip_y) != int(parta_info["CHIP_Y_CNT"]):
        amount_info = [False,len(chip_x), len(chip_y), int(parta_info["CHIP_X_CNT"]), int(parta_info["CHIP_Y_CNT"])]
        print('XY Type num error!')
        return amount_info


    print('int(parta_info["CHIP_Y_CNT"]) * int(parta_info["CHIP_X_CNT"]): ', int(parta_info["CHIP_Y_CNT"]) * int(parta_info["CHIP_X_CNT"]))
    print("actual", sqc_file.shape[0])

    # 維度確認
    if (int(parta_info["CHIP_Y_CNT"]) * int(parta_info["CHIP_X_CNT"]) != sqc_file.shape[0]):
        print('fillup df')
        # 生成空矩陣
        full_chip = [[np.nan] + [i, j] + (ins_cnt-3)*[np.nan] for i in chip_x for j in chip_y]
        full_df = pd.DataFrame(data = full_chip, columns=sqc_file.columns.tolist())
        print(full_df)
        # 補齊矩陣
        sqc_file = sqc_file.append(full_df, ignore_index=True).drop_duplicates(subset = ['COORDINATE_X', 'COORDINATE_Y'])
        print("fillup total time: ", start - time.time())

    file_name = parta_info["CARRIER_TYPE"] + "#" + parta_info["LED_TYPE"] + "#" + parta_info["WAFER_ID"] + "#" + parta_info["WAFER_SIZE"] + "#" + parta_info["CHIP_Y_CNT"] + "#" +parta_info["CHIP_X_CNT"] + "#v" + '000.csv'

    sqc_file = sqc_file.sort_values(by=['COORDINATE_X', 'COORDINATE_Y'], ascending=[True, True]).reset_index(drop=True)

    sqc_file.to_csv(file_path_in + file_name, index=False)
    print('parse_partB done!')
    return [True]

# 更新計算用設定json檔案
def update_wma_json(parta_info, MODEL_NO):
    print('update_wma_json start')
    try:
        model_spec = pd.read_csv(r'./Data_Archived/model_spec.csv')
        new_ver_dict = {}

        file_open = open("./WMA_V3/WMA.json", "r")
        wma_json = json.load(file_open)
        file_open.close()

        # parta info to json
        wma_json["SQC_IN"]["chip_x"] = parta_info['CHIP_Y_CNT']
        wma_json["SQC_IN"]["chip_y"] = parta_info['CHIP_X_CNT']
        wma_json["SQC_IN"]["wafer_area"] = parta_info['AREA_CNT']
        wma_json["SQC_IN"]["wafer_id"] = parta_info['WAFER_ID']
        wma_json["SQC_IN"]["MODEL_NO"] = MODEL_NO
        print('wma_json["SQC_IN"]["MODEL_NO"]: ', wma_json["SQC_IN"]["MODEL_NO"])
        print("MODEL_NO: ", MODEL_NO)
        wma_json["QC_JUDGE"] = {}

        # spec info to josn
        for i in range(model_spec.shape[0]):
            if model_spec['MODEL_NO'][i] in new_ver_dict.keys() and (int(model_spec['SPEC_VER'][i][1:]) <= int(new_ver_dict[model_spec['MODEL_NO'][i]][1:])):
                continue
            else:
                new_ver_dict[model_spec['MODEL_NO'][i]] = model_spec['SPEC_VER'][i]

        temp = model_spec[model_spec['MODEL_NO'].str.contains(MODEL_NO) & model_spec['SPEC_VER'].str.contains(new_ver_dict[MODEL_NO])]
        wma_json["AREA_JUDGE"]["pixel_repeat_x"] = list(temp["PIXEL_REPEAT_X"])[0]
        wma_json["AREA_JUDGE"]["pixel_repeat_y"] = list(temp["PIXEL_REPEAT_Y"])[0]
        wma_json["AREA_JUDGE"]["area_repeat_x"] = list(temp["AREA_REPEAT_X"])[0]
        wma_json["AREA_JUDGE"]["area_repeat_y"] = list(temp["AREA_REPEAT_Y"])[0]
        
        
        for ins_type in list(temp["INS_TYPE"]):
            ins_info_dict = {}
            ins_info_dict["item_name"] = ins_type
            ins_info_dict["min_set"] = list(temp[temp["INS_TYPE"].str.contains(ins_type)]["SPEC_MIN"])[0]
            ins_info_dict["max_set"] = list(temp[temp["INS_TYPE"].str.contains(ins_type)]["SPEC_MAX"])[0]
            wma_json["QC_JUDGE"][ins_type] = ins_info_dict
        # print(wma_json)
        # update json
        file_update = open("./WMA_V3/WMA.json", "w")
        json.dump(wma_json, file_update)
        file_update.close()
        print('update_wma_json end')
    
    except Exception as e:
        print(e)

# 離線版手動上傳qc in資料
@api_view(['POST'])
def get_upload_file(request):
    print('get_upload_file start!!!')
    start_time = time.time()
    # 儲存下載檔案
    file_obj = request.data['qcfile']
    file_path = './upload_temp/' + request.data['qcfile'].name
    # print(request.data['input_id'])
    try:
        with open(file_path, 'wb+') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        print('total time: ', start_time-time.time())
    
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    # 確認input_id是否一致
    parta_info = parse_partA(file_path)
    if request.data['input_id'] == parta_info["WAFER_ID"]:
        print('success!' + file_path)
        return Response(file_path, status=status.HTTP_200_OK)
    else:
        print('fail! remove file')
        os.remove(file_path)
        return Response(False, status=status.HTTP_200_OK)


# 離線版手動上傳used in資料
@api_view(['POST'])
def get_used_file(request):
    print('usedin_confirm start!!!')
    start_time = time.time()
    # 儲存下載檔案
    file_obj = request.data['usefile']
    file_path = './upload_temp/' + request.data['usefile'].name
    # print(request.data['input_id'])
    try:
        with open(file_path, 'wb+') as f:
            for chunk in file_obj.chunks():
                f.write(chunk)
        print('total time: ', start_time-time.time())
    
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
    
    wafer_list = pd.read_csv(r'./Data_Archived/wafer_list.csv')

    if request.data['usefile'].name.split("/")[-1].split("#")[2] in wafer_list['WAFER_ID'].tolist():
        print('start run WMA!')
        wafer_id = request.data['usefile'].name.split("/")[-1].split("#")[2]
        print('wafer_id: ', wafer_id)
        WMA.update_USE2JUDGE_file(wafer_id = wafer_id)
        return Response(request.data['usefile'].name.split("/")[-1].split("#")[2], status=status.HTTP_200_OK)
    else:
        return Response(False, status=status.HTTP_200_OK)

# 編輯與刪除wafer list資料
@api_view(['POST'])
def edit_wafer_lsit(request):
    data = pd.read_csv(r'./Data_Archived/wafer_list.csv')
    backup_data = pd.read_csv(r'./Data_Archived/wafer_list_history.csv')
    parta_info = {
    "CARRIER_TYPE": "",
    "LED_TYPE": "",
    "AREA_CNT": "",
    "WAFER_ID": "",
    "WAFER_SIZE": "",
    "CHIP_X_CNT": "",
    "CHIP_Y_CNT": "",
    "LED_PITCH_X": "",
    "LED_PITCH_Y": ""
    }

    # delete path
    OUTPUT = './WMA_V3/OUTPUT/'
    WMA_MAP_JSON = './WMA_V3/WMA_MAP_JSON/JSON_HISTORY/'
    USE_HISTORY = './WMA_V3/data/1_USE_HISTORY/'
    QC_JUDGE_ORGIN = "./WMA_V3/data/2_QC_JUDGE/2_QC_JUDGE_ORGIN/"
    QC_JUDGE_JUDGE = "./WMA_V3/data/2_QC_JUDGE/2_QC_JUDGE_JUDGE/"
    QC_JUDGE_HISTORY = "./WMA_V3/data/2_QC_JUDGE/2_QC_JUDGE_HISTORY/"
    QC_OUT = "./WMA_V3/data/3_QC_OUT/"
    QC_1D_OUT = "./WMA_V3/data/3_QC_1D_OUT/"
    file_path = [WMA_MAP_JSON, USE_HISTORY, QC_JUDGE_ORGIN, QC_JUDGE_JUDGE, QC_JUDGE_HISTORY, QC_OUT, QC_1D_OUT]

    # del via wafer id
    if request.data['action'] == 'delete':
        # del wafer list
        backup_data =  backup_data.append(data[data['WAFER_ID'].isin([request.data['ID']])], ignore_index=True)
        data = data[~data['WAFER_ID'].isin([request.data['ID']])]
        data.to_csv('./Data_Archived/wafer_list.csv', mode='w', index =False)
        backup_data.to_csv('./Data_Archived/wafer_list_history.csv', mode='w', index =False)

        try:
            # del actual data
            for path in file_path:
                print(path)
                for (root, dirs, files) in os.walk(path):
                    print(files)
                    for file in files:
                        print(file)
                        if request.data['ID'] in file:
                            os.remove(os.path.join(root, file))
            for (root, dirs, files) in os.walk(OUTPUT):
                for dird in dirs:
                    print(dird)
                    if request.data['ID'] in dird:
                        shutil.rmtree(os.path.join(root, dird))
            return Response('delete success', status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

    # edit via wafer id & model no
    if request.data['action'] == 'edit':
        try:
            data.loc[data['WAFER_ID'] == request.data['ID'], 'MODEL_NO'] = request.data['MODEL_NO']
            parta_info["CARRIER_TYPE"] = list(data.loc[data['WAFER_ID'] == request.data['ID']]["CARRIER_TYPE"])[0]
            parta_info["LED_TYPE"] = list(data.loc[data['WAFER_ID'] == request.data['ID']]["LED_TYPE"])[0]
            parta_info["AREA_CNT"] = list(str(data.loc[data['WAFER_ID'] == request.data['ID']]["AREA_CNT"]))[0]
            parta_info["WAFER_ID"] = list(data.loc[data['WAFER_ID'] == request.data['ID']]["WAFER_ID"])[0]
            parta_info["WAFER_SIZE"] = list(str(data.loc[data['WAFER_ID'] == request.data['ID']]["WAFER_SIZE"]))[0]
            parta_info["CHIP_X_CNT"] = list(str(data.loc[data['WAFER_ID'] == request.data['ID']]["CHIP_X_CNT"]))[0]
            parta_info["CHIP_Y_CNT"] = list(str(data.loc[data['WAFER_ID'] == request.data['ID']]["CHIP_Y_CNT"]))[0]
            parta_info["LED_PITCH_X"] = list(str(data.loc[data['WAFER_ID'] == request.data['ID']]["LED_PITCH_X"]))[0]
            parta_info["LED_PITCH_Y"] = list(str(data.loc[data['WAFER_ID'] == request.data['ID']]["LED_PITCH_Y"]))[0]
            print(parta_info)
            update_wma_json(parta_info, request.data['MODEL_NO'])
            WMA.update_USE2JUDGE_file(wafer_id = request.data['ID'])
            data.to_csv('./Data_Archived/wafer_list.csv', mode='w', index =False)
            return Response('edit success', status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(str(e), status =status.HTTP_400_BAD_REQUEST)


# 線上版用之自動獲取qc in資料
# user 需手動輸入要使用之wafer id
@api_view(['POST'])
def id_exist_check_v2(request):
    # handel json decode error
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)

    wafer_list = pd.read_csv(r'./Data_Archived/wafer_list.csv')

    try:
        if request_data["ID"] not in wafer_list['WAFER_ID'].tolist():
            path = './upload_temp/'
            for (root, dirs, files) in os.walk(path):
                file_exist = [string for string in files if request_data["ID"] in string]
                if len(file_exist) >= 1:
                    parta_info = parse_partA(path+file_exist[0])
                    if request.data['ID'] == parta_info["WAFER_ID"]:
                        return Response([True, path+file_exist[0]], status=status.HTTP_200_OK)
                    else:
                        return Response([False, "not consist with parta id!"], status=status.HTTP_200_OK)
                else:
                    return Response([False, "not in directory!"], status=status.HTTP_200_OK)
        else:
            return Response([False, "already in wafer list!"], status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response(str(e), status=status.HTTP_400_BAD_REQUEST)

# paring 選area*6
@api_view(['POST'])
def paring_select(request):
    # handel json decode error
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)
    
    wafer_area_list = pd.read_csv(r'./Data_Archived/wafer_area_list.csv')
    paring_result = pd.DataFrame(data=[], columns=["wafer_id", "sx", "sy", "MODEL_NO", "TFTID"])
    
    if len(request_data["ID"]) > 6:
        return Response("Area over 6!", status=status.HTTP_200_OK)
    
    for i in range(len(request_data["ID"])):
        if wafer_area_list[(wafer_area_list["wafer_id"].str.contains(request_data["ID"][i])) & (wafer_area_list["sx"] == (request_data["sx"][i])) & (wafer_area_list["sy"] == (request_data["sy"][i]))].empty:
            error_txt = "Area not Exist!","ID: ", request_data["ID"][i], "sx: ", request_data["sx"][i], "sy: ", request_data["sy"][i]
            return Response(error_txt, status=status.HTTP_200_OK)
        
        elif list(wafer_area_list[(wafer_area_list["wafer_id"].str.contains(request_data["ID"][i])) & (wafer_area_list["sx"] == (request_data["sx"][i])) & (wafer_area_list["sy"] == (request_data["sy"][i]))][Status] == "used"):
            error_txt = "Area already used!","ID: ", request_data["ID"][i], "sx: ", request_data["sx"][i], "sy: ", request_data["sy"][i]
            return Response(error_txt, status=status.HTTP_200_OK)
        else:
            tmp = [request_data["ID"][i], request_data["sx"][i], request_data["sy"][i], request_data["MODEL_NO"], request_data["TFTID"]]
            paring_result.loc[len(paring_result)] = tmp
            wafer_area_list.Status[(wafer_area_list["wafer_id"].str.contains(request_data["ID"][i])) & (wafer_area_list["sx"] == (request_data["sx"][i])) & (wafer_area_list["sy"] == (request_data["sy"][i]))] = "used"
    print(paring_result)
    result_name = "./WMA_V3/data/6_PARING_RESULT/" + request_data["MODEL_NO"] + "_" + str(request_data["TFTID"]) + "_" + str(time.strftime("%Y%m%d%H%M%S")) + ".csv"
    wafer_area_list.to_csv('./Data_Archived/wafer_area_list.csv', mode='w', index = False)
    paring_result.to_csv(result_name)        
    return Response(result_name)

# FOR ONLINE

# Execute after Response
class ResponseThen(Response):
    def __init__(self, data, then_callback, **kwargs):
        super().__init__(data, **kwargs)
        self.then_callback = then_callback

    def close(self):
        super().close()
        self.then_callback()

@api_view(['POST'])
def MES_QC_IN(request):
    # handel json decode error
    try:
        request_data = json.loads(request.body)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)
    
    # build status list for each trx_sn
    qc_list = []
    trx_sn = request_data["trx"]["trx_sn"]
    log_id = request_data["trx"]["log_id"]
    lm_time = request_data["trx"]["lm_time"]
    in_path = './upload_temp/'
    
    for material_info in  request_data["trx"]["material_infos"]["material_info"]:
        qc_dic = {}
        qc_dic["trx_sn"] = trx_sn
        qc_dic["log_id"] = log_id
        qc_dic["lm_time"] = lm_time
        qc_dic["wafer_id"] = material_info["wafer_id"]
        qc_dic["model_no"] = material_info["model_no"]
        qc_dic["status"] = ""
        qc_list.append(qc_dic)
    tmp_df = pd.DataFrame(qc_list)
    tmp_df.lm_time.apply(str)
    print(tmp_df['lm_time'])
    
    # check file exist
    for i in qc_list:
        for (root, dirs, files) in os.walk(in_path):
            if len([string for string in files if i["wafer_id"] in string]) > 0:
                i['status'] = 'wait for judging!'
            else:
                i['status'] = 'not in dir!'
    
    # update to status list
    status_list = pd.read_csv(r'./Data_Archived/wafer_status_list.csv')
    # for i in qc_list:
    #     status_list = status_list.append(i, ignore_index=True)
    # status_list.to_csv('./Data_Archived/wafer_status_list.csv', mode='w', index=False)
    tmp_df.to_csv('./Data_Archived/wafer_status_list.csv', mode = 'a', index=False, header=False)
    
            
    return Response(True)
    
        

# input: wafer_id & trx_sn
@api_view(['POST'])
def status_check(request):
    # handel json decode error
    try:
        request_data = json.loads(request.body)
        # print(request_data)
    except json.decoder.JSONDecodeError as e:
        py_dict = {'error_msg': str(e)}
        json_dict = json.dumps(py_dict)
        return Response(json_dict, status=status.HTTP_400_BAD_REQUEST)
    
    # status list for proccess control
    status_list = pd.read_csv(r'./Data_Archived/wafer_status_list.csv')
    # Output format
    with open('./TRX_Format/TxMaterialAnalyzeReq-O.json') as f:
        output_format = json.load(f)
    
    
    # build trx_sn list for each request
    qc_list = []
    trx_sn = request_data["trx"]["trx_sn"]
    log_id = request_data["trx"]["log_id"]
    lm_time = request_data["trx"]["lm_time"]
    in_path = './upload_temp/'
    
    for material_info in  request_data["trx"]["material_infos"]["material_info"]:
        qc_dic = {}
        qc_dic["trx_sn"] = trx_sn
        qc_dic["log_id"] = log_id
        qc_dic["lm_time"] = lm_time
        qc_dic["wafer_id"] = material_info["wafer_id"]
        qc_dic["model_no"] = material_info["model_no"]
        qc_dic["status"] = ""
        qc_dic["error_msg"] = ""
        qc_list.append(qc_dic)
    

    # check file exist
    for i in qc_list:
        for (root, dirs, files) in os.walk(in_path):
            print(len([string for string in files if i["wafer_id"] in string]))
            if len([string for string in files if i["wafer_id"] in string]) == 0:
                i['status'] = 'ERROR'  
                i['error_msg'] = 'no such file'
    print(qc_list)
    
    
    # 若TRX_SN已存在
    if trx_sn in status_list.values:
        print("exist")
        # 檢查資料庫的 WAFER_ID 與傳入是否相符
        current_trx_sn = status_list[status_list['trx_sn'].str.contains(trx_sn)]
        id_list_db = list(current_trx_sn['wafer_id'])
        id_list_request = []
        for i in qc_list:
            id_list_request.append(i['wafer_id'])
        if set(id_list_db) != set(id_list_request):
            return Response("TRX_SN與WAFER ID不符合", status=status.HTTP_400_BAD_REQUEST)

        # 檢查資料庫的 WAFER 狀態
        output_format["trx"]["log_id"] = log_id
        output_format["trx"]["trx_sn"] = trx_sn
        output_format["trx"]["lm_time"] = lm_time
        tmp_list = []
        for row in current_trx_sn.itertuples(index=False):
            tmp = {}
            
            # 當狀態為 COMPLETE , 回傳 meterial_info
            if row.status == "COMPLETE":
                tmp["wafer_id"] = row.wafer_id
                tmp["status"] = row.status
                tmp["spec_id"] = "COMPLETE_TESTING"
                tmp["map_id"] = "COMPLETE_TESTING"
                tmp["map_path"] = row.ox_file_path
                tmp["judge_user"] = "COMPLETE_TESTING"
                tmp["judge_time"] = "COMPLETE_TESTING"
                tmp["judge_comment"] = "COMPLETE_TESTING"
            
            # 當狀態為 PROCESSING, 報錯 (回報資料庫記錄的 TRX_SN, LM_TIME)    
            if row.status == "PROCESSING":
                tmp["wafer_id"] = row.wafer_id
                tmp["status"] = row.status
                tmp["link"] = "WAIT_TESTING"
                
            # 當狀態為 ERROR, (回報資料庫記錄的 ERROR MESSAGE -> rtn_code, rtn_msg)
            if row.status == "ERROR":
                tmp["wafer_id"] = row.wafer_id
                tmp["status"] = row.status
                tmp["error_msg"] = "ERROR_TESTING"
            tmp_list.append(tmp)
            output_format["trx"]["material_infos"]["material_info"] = tmp_list
        return Response(output_format)

    # 若TRX_SN不存在
    if trx_sn not in status_list.values:
        print("not exist")
        for i in qc_list:
            tmp = {}
            # 若無檔案則跳過
            if i['status'] == 'ERROR' and i['error_msg'] == 'no such file':
                pass
            
            # 檢查資料庫是否有存在與傳入相符的 WAFER_I
            # 若 WAFER_ID 存在
            if not status_list[status_list['wafer_id'].str.contains(i['wafer_id'])].empty:
                print('new trx_sn & wafer exist')
                tmp_df = status_list[status_list['wafer_id'].str.contains(i['wafer_id'])]
                tmp_df['lm_time'] = tmp_df['lm_time'].apply(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S.%f"))
                
                # 最新版status為complete
                if tmp_df[tmp_df['lm_time'] == max(tmp_df['lm_time'])]['status'].values[0] == 'COMPLETE':
                    print("執行新一次的judging")
                
                # 最新版status為processing or error
                if tmp_df[tmp_df['lm_time'] == max(tmp_df['lm_time'])]['status'].values[0] == 'PROCESSING':
                    i['status'] = 'ERROR'  
                    i['error_msg'] = 'last one still processing' + tmp_df[tmp_df['lm_time'] == max(tmp_df['lm_time'])]['trx_sn'].values[0]

                if tmp_df[tmp_df['lm_time'] == max(tmp_df['lm_time'])]['status'].values[0] == 'ERROR':
                    i['status'] = 'ERROR'  
                    i['error_msg'] = 'last one error' + tmp_df[tmp_df['lm_time'] == max(tmp_df['lm_time'])]['error_msg'].values[0]
            
            # 若 WAFER_ID 不存在
            if status_list[status_list['wafer_id'].str.contains(i['wafer_id'])].empty:
                print(i['wafer_id'], "empty")
                tmp_df = pd.DataFrame(qc_list)
                tmp_df.lm_time.apply(str)
                tmp_df.to_csv('./Data_Archived/wafer_status_list.csv', mode = 'a', index=False, header=False)    
    

    return Response(True)


        
@api_view(['GET'])
def some_view(request):
    # ...code to run before response is returned to client

    def do_after():
        # ...code to run *after* response is returned to client
        while True:
            print('from do after')

    return ResponseThen("from some view", do_after, status=status.HTTP_200_OK)
