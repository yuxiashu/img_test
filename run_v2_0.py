from copy import deepcopy
from flask import Flask

from paddleocr import PaddleOCR
import re
import os  
import json
import time
from PIL import Image, ImageDraw
from utils import *
import glob

import base64
import requests
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
sys.path.append('./')

app = Flask(__name__)
# 文本识别？->作用
@app.route('/screen_recg',methods=['GET,POST'])

def text_rec():

    ocr = PaddleOCR(det_model_dir="./img_rec/inference/ch_ppocr_mobile_v2.0_det_infer/",
                    rec_model_dir="./img_rec/inference/ch_ppocr_mobile_v2.0_rec_infer/",
                    cls_model_dir="./img_rec/inference/ch_ppocr_mobile_v2.0_cls_infer/",
                    use_angle_cls=True, use_gpu=False)

    #yaml_file = r"D:\CodeSet_User_Example\python\form-generator\AI\img_rec\config.yaml"
    yaml_file = 'config.yaml'
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(os.path.dirname('./'))
    print(current_dir,'current——dir<<<<<')
    config = load_yaml(yaml_file)
    
    # patterns = "单行文本|多行文本|评分"
    patterns = config["patterns"]

    # row_num = 36
    row_num = config["row_num"]
    
    dft_json_dir = config["json_dir"]
    json_std_component = os.path.join(dft_json_dir+'sample0.json')
    with open(json_std_component,"r", encoding="utf-8") as sample_json:
    #with open(r"D:\CodeSet_User_Example\python\form-generator\AI\img_rec\json\sample0.json", "r", encoding="utf-8") as sample_json:
        sample_dict = json.load(sample_json)
    
    dic = {}
    output_list = []

    # img_file = glob.glob("/home/ai/AI/img_rec/imgs/*")
    #img_file = glob.glob(r"./img_rec/test7.jpg")
    img_file =glob.glob(r"D:\CodeSet_User_Example\python\form-generator\AI\img_rec\img_rec\test7.jpg")
    
    if not img_file:
        print('<ERROR no img>')
        return output_list, sample_dict["config"]

    for file_path in img_file:
        img_pil = Image.open(file_path)

        color_pil = img_pil.convert("RGB")
        gray_pil = img_pil.convert("L")

        w, h = color_pil.size
        #print(h,'<<<<height')
        if h<180:
            row_num = 15
        elif(h<360):
            row_num = 18
        elif h<720:
            row_num = 27
        

        # detect and recognize text lines with angle
        # return list of [[a, b, c, d], (text, confidence)]
        results = ocr.ocr(file_path, cls=True)
        layout_list = [[] for i in range(row_num)]
        #print('text>>>>>',results)
        
        for rect in results:
            
            text, confidence = rect[1]
            y = 0
            for i in range(4):
                y += rect[0][i][1]
                
            y = int(y / 4)
            
            if re.search(patterns, text, re.IGNORECASE):
                (head, tail) = re.search(patterns, text, re.IGNORECASE).span()
                print("Recognize text \"" + text + "\" as component \"" + text[head:tail] + "\"")
                for item in sample_dict["list"]:
                    if text[head:tail] == item["name"]:
                        output_item = item
                        time.sleep(1e-4)
                        time_stamp = str(int(time.time() * 1000))
                        output_item["options"]["remoteFunc"] = "func_" + time_stamp
                        output_item["options"]["remoteOption"] = "option_" + time_stamp
                        output_item["key"] = time_stamp
                        output_item["model"] = output_item["type"] + "_" + time_stamp
                        layout_list[int(y / (h / row_num))].append(output_item)
                        #print('int(y / (h / row_num))',int(y / (h / row_num)))
                        #print(layout_list,'<<<<<<layout_list')
                        # output_list.append(output_item)
                        break
                #print('layout_list>>>>》》》》》》》',layout_list)
            
        for item in sample_dict["list"]:
            if item["name"] == "栅格布局":
                grid = item
                break
               
        for i in range(row_num):
            if len(layout_list[i]) > 1:
                new_grid = deepcopy(grid)
                
                col = {} 

                for item in layout_list[i]:
                    
                    time_stamp = str(int(time.time() * 1000))
                    new_grid["options"]["remoteFunc"] = "func_" + time_stamp
                    new_grid["options"]["remoteOption"] = "option_" + time_stamp
                    new_grid["options"]["flex"] = True
                    new_grid["options"]["customClass"] = ""

                    new_grid["key"] = time_stamp
                    new_grid["model"] = new_grid["type"] + "_" + time_stamp
                    col['type'] = 'col'
                    col["options"] = {}
                    col["options"]["span"] = 24
                    col["list"] = [item]
                    time.sleep(1e-4)
                    time_stamp = str(int(time.time() * 1000))
                    col['key'] = time_stamp
                    new_grid['columns'].append(deepcopy(col))
                    # print('new_grid[columns]》》》》',new_grid['columns'],'\n')
                output_list.append(new_grid)
            else:
                if len(layout_list[i]) > 0:
                    output_list.append(layout_list[i][0])

    dic["list"] = output_list
    dic["config"] = sample_dict["config"]
    dic = json.dumps(dic, ensure_ascii=False)
    with open(dft_json_dir + "components.json", "w", encoding="utf-8") as output_json:
    #with open(r"D:\CodeSet_User_Example\python\form-generator\AI\img_rec\json\components.json", "w", encoding="utf-8") as output_json:
        output_json.write(dic)

    #return output_list, sample_dict["config"]
    return dic

def hw_rec(files):

    yaml_file = "img_rec/config.yaml"
    config = load_yaml(yaml_file)

    # patterns = "单行文本|多行文本|评分"
    patterns = config["patterns"]

    # row_num = 16
    row_num = config["row_num"]

    json_dir = config["json_dir"]
    with open(json_dir + "sample0.json", "r", encoding="utf-8") as sample_json:
        sample_dict = json.load(sample_json)

    dic = {}
    output_list = []

    for index, file in files.items():
        img = file.read()
        byte_stream = io.BytesIO(img)
        img_pil = Image.open(byte_stream)

        color_pil = img_pil.convert("RGB")
        color_pil = crop(image_binarization_part_situation(color_pil))

        img_path = os.getcwd() + '/img_rec/imgs/' + file.filename
        ratio = color_pil.size[0] / color_pil.size[1]
        color_pil = color_pil.resize((int(720 * ratio), 720))
        color_pil.save(img_path)

        w, h = color_pil.size

        # detect and recognize text lines with angle
        # return dict of
        # "predictions": [
        #     {
        #         "detection_multiclass_scores": [],
        #         "detection_classes": [],
        #         "num_detections": 40,
        #         "image_info": [],
        #         "detection_boxes": [],
        #         "detection_scores": [],
        #         "detection_classes_as_text": [],
        #         "key": []
        #     }
        # ]
        results = container_predict(img_path, "test")["predictions"][0]

        count = 0
        for score in results["detection_scores"]:
            if score > config["threshold"]:
                count += 1

        layout_list = [[] for _ in range(row_num)]
        label2name = config["label2name"]

        xs = []
        for i in range(count):
            xs.append(results["detection_boxes"][i][1])
        index_x = sort_x(xs)

        for i in range(count):
            text = results["detection_classes_as_text"][index_x[i]]
            text = label2name[text]
            y, x = results["detection_boxes"][index_x[i]][:2]
            if re.search(patterns, text, re.IGNORECASE):
                (head, tail) = re.search(patterns, text, re.IGNORECASE).span()
                print("Recognize text \"" + text + "\" as component \"" + text[head:tail] + "\"")
                for item in sample_dict["list"]:
                    if text[head:tail] == item["name"]:
                        output_item = item
                        time.sleep(1e-4)
                        time_stamp = str(int(time.time() * 1000))
                        output_item["options"]["remoteFunc"] = "func_" + time_stamp
                        output_item["options"]["remoteOption"] = "option_" + time_stamp
                        output_item["key"] = time_stamp
                        output_item["models"] = output_item["type"] + "_" + time_stamp
                        layout_list[int(y * row_num)].append(output_item)
                        # output_list.append(output_item)
                        break

        for item in sample_dict["list"]:
            if item["name"] == "栅格布局":
                grid = item
                break

        for i in range(row_num):
            if len(layout_list[i]) > 1:
                new_grid = deepcopy(grid)
                for item in layout_list[i]:
                    time_stamp = str(int(time.time() * 1000))
                    new_grid["options"]["remoteFunc"] = "func_" + time_stamp
                    new_grid["options"]["remoteOption"] = "option_" + time_stamp
                    new_grid["key"] = time_stamp
                    new_grid["models"] = new_grid["type"] + "_" + time_stamp
                    new_column = {}
                    new_column["span"] = 24
                    new_column["list"] = [item]
                    new_grid["columns"].append(new_column)
                output_list.append(new_grid)
            else:
                if len(layout_list[i]) > 0:
                    output_list.append(layout_list[i][0])

    dic["list"] = output_list
    dic["config"] = sample_dict["config"]
    dic = json.dumps(dic, ensure_ascii=False)
    with open(json_dir + "components.json", "w", encoding="utf-8") as output_json:
        output_json.write(dic)

    return dic


'''
测试百度预训练
'''
def test():
    # 测试PaddleOCR?
    # det_model_dir->自己训练的检测模型；
    # rec_model_dir->自己训练的识别模型；
    # cls_model_dir->自己训练的分类模型；
    # use_angle_cls->是否加载分类模型；
    ocr = PaddleOCR(det_model_dir="./img_rec/inference/ch_ppocr_server_v2.0_det_infer/",
                    rec_model_dir="./img_rec/inference/ch_ppocr_server_v2.0_rec_infer/",
                    cls_model_dir="./img_rec/inference/ch_ppocr_mobile_v2.0_cls_infer/",
                    use_angle_cls=True, use_gpu=False)
    test_png_path = r"./img_rec/test5.jpg"
    # test_png_path = r"E:\360MoveData\Users\jqj\Desktop\DXC实习\Mydemo\DataProcess\data\test\1626145697.9337728.png"
    results = ocr.ocr(test_png_path, cls=True)
    print(results)


"""
EasyDL 图像分类 调用模型公有云API Python3实现
暂时密钥'等是个人私钥，免费使用1000次'
"""

# def Api_rec():
#     # 目标图片的 本地文件路径，支持jpg/png/bmp格式
#     # IMAGE_FILEPATH = "【您的测试图片地址，例如：./example.jpg】"
#     IMAGE_FILEPATH = r"D:\Users_\test\Downloads\temp\ocr_test.jpg"

#     # 可选的请求参数
#     # top_num: 返回的分类数量，不声明的话默认为 6 个
#     PARAMS = {"top_num": 10}

#     # 服务详情 中的 接口地址
#     # MODEL_API_URL = "【您的API地址】"
#     MODEL_API_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/detection/SketchAI1"

#     # 调用 API 需要 ACCESS_TOKEN。若已有 ACCESS_TOKEN 则于下方填入该字符串
#     # 否则，留空 ACCESS_TOKEN，于下方填入 该模型部署的 API_KEY 以及 SECRET_KEY，会自动申请并显示新 ACCESS_TOKEN
#     ACCESS_TOKEN = "24.6647dc648b8882ac4e568ba1d329628a.2592000.1628824126.282335-24544338"
#     API_KEY = "LyZbjIwSd9BK034en8U0mAdo"
#     SECRET_KEY = "YdVEUtGjhwIYgj0YVt3LtKWgdKy9cW65"

#     # 读取目标图片,将 BASE64 编码后图片的字符串填入 PARAMS 的 'image' 字段
#     with open(IMAGE_FILEPATH, 'rb') as f:
#         base64_data = base64.b64encode(f.read())
#         base64_str = base64_data.decode('UTF8')
#     PARAMS["image"] = base64_str

#     # 获取ACCESS_TOKEN
#     if not ACCESS_TOKEN:
#         print("ACCESS_TOKEN 为空，调用鉴权接口获取TOKEN")
#         auth_url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={}&client_secret={}".format(
#             API_KEY, SECRET_KEY)
#         auth_resp = requests.get(auth_url)
#         auth_resp_json = auth_resp.json()
#         ACCESS_TOKEN = auth_resp_json["access_token"]
#         print("新 ACCESS_TOKEN: {}".format(ACCESS_TOKEN))
#     else:
#         print("使用已有 ACCESS_TOKEN")

#     #  向模型接口 'MODEL_API_URL' 发送请求"
#     request_url = "{}?access_token={}".format(MODEL_API_URL, ACCESS_TOKEN)
#     response = requests.post(url=request_url, json=PARAMS)
#     response_json = response.json()
#     # 转换成字符打印查看
#     response_str = json.dumps(response_json, indent=4, ensure_ascii=False)
#     print(response_str)

#     # 将json转化为dict解析返回的数据结果
#     # html_json = json.loads(response_str)
#     json_out = {}
#     labels_list = []
#     for j in response_json["results"]:
#         _temp = {}
#         _temp["name"] = j["name"]
#         _temp["x1"] = j["location"]["left"]
#         _temp["y1"] = j["location"]["top"]
#         _temp["x2"] = j["location"]["left"] + j["location"]["width"]
#         _temp["y2"] = j["location"]["top"] + j["location"]["height"]
#         labels_list.append(_temp)
#     json_out["labels"] = labels_list
#     json_out = json.dumps(json_out)
#     print(json_out, type(json_out))


if __name__ == "__main__":
    # Api_rec()
    text_rec()
    # test()