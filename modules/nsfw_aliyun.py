import os
from PIL import Image, ImageFilter
import cv2
from aliyunsdkcore import client
from aliyunsdkgreen.request.v20180509 import ImageSyncScanRequest,ImageAsyncScanRequest
from aliyunsdkcore.profile import region_provider
from aliyunsdkgreenextension.request.extension import ClientUploader
from aliyunsdkgreenextension.request.extension import HttpContentHelper

import json
import uuid

from modules import paths

key_id = os.environ.get('GREEN_API_KEY_ID')
key_secret = os.environ.get('GREEN_API_KEY_SECRET')

clt = client.AcsClient(key_id, key_secret,"cn-beijing")
region_provider.modify_point('Green', 'cn-beijing', 'green.cn-beijing.aliyuncs.com')

watermark_image= "nsfw-wm.png"

model_dir = "nsfw"
watermark_image= "nsfw-wm.png"
watermark_image_path = os.path.join(paths.models_path, model_dir, watermark_image)
watermark = cv2.imread(watermark_image_path, cv2.IMREAD_UNCHANGED)

def nsfw_detect(image_path):

    # request = ImageAsyncScanRequest.ImageAsyncScanRequest()
    request = ImageSyncScanRequest.ImageSyncScanRequest()
    request.set_accept_format('JSON')

    uploader = ClientUploader.getImageClientUploader(clt)
    #url = uploader.uploadFile(image_path)
    url = "http://s7.bailusoft.com:7860/file=" + image_path

    task = {
        "dataId": str(uuid.uuid1()),
        "url": url
    }

    request.set_content(json.dumps({"tasks": [task], "scenes": ["porn"]}))
    response = clt.do_action_with_exception(request)
    print(response)
    result = json.loads(response)
    if 200 == result["code"]:
        taskResults = result["data"]
        for taskResult in taskResults:
            if 200 == taskResult["code"]:
                sceneResults = taskResult["results"]
                for sceneResult in sceneResults:
                    scene = sceneResult["scene"]
                    suggestion = sceneResult["suggestion"]
                    label = sceneResult["label"]
                    print(label)
                    print(suggestion)
                    if suggestion == "block": # and label== "porn" :
                        return True
    return False
                
    # if 200 == result["code"]:
    #     taskResults = result["data"]
    #     for taskResult in taskResults:
    #         if(200 == taskResult["code"]):
    #             taskId = taskResult["taskId"]
    #             # 保存taskId。间隔一段时间后使用taskId查询检测结果。
    #             print(taskId)

def nsfw_upload_detect(image_path):

    request = ImageSyncScanRequest.ImageSyncScanRequest()
    request.set_accept_format('JSON')

    uploader = ClientUploader.getImageClientUploader(clt)
    url = uploader.uploadFile(image_path)

    task = {
        "dataId": str(uuid.uuid1()),
        "url": url
    }

    request.set_content(json.dumps({"tasks": [task], "scenes": ["porn"]}))
    response = clt.do_action_with_exception(request)
    print(response)

    nsfw = True
    porn = False

    result = json.loads(response)
    if 200 == result["code"]:
        taskResults = result["data"]
        for taskResult in taskResults:
            if 200 == taskResult["code"]:
                sceneResults = taskResult["results"]
                for sceneResult in sceneResults:
                    scene = sceneResult["scene"]
                    suggestion = sceneResult["suggestion"]
                    label = sceneResult["label"]
                    print(label)
                    print(suggestion)
                    if suggestion == "pass":
                        nsfw = False 
                    elif label == "porn":
                        porn = True

    return nsfw, porn 
                

def nsfw_blur(src_image_path):
    print('blur image file:', src_image_path)
    
    # Open the source and watermark images
    src_image = Image.open(src_image_path)
    watermark_image = Image.open(watermark_image_path)
    if src_image is None or watermark_image is None:
        print('Failed to open the source or watermark image')
        return
    
    src_image = src_image.filter(ImageFilter.GaussianBlur(radius = 30))
    # Calculate the watermark dimensions based on the source image's size and aspect ratio
    src_width, src_height = src_image.size
    watermark_width, watermark_height = watermark_image.size

    # Resize the watermark image to fit the source image
    if src_height < src_width:
        new_watermark_height = int(src_height/6)
        new_watermark_width = int(new_watermark_height * (watermark_width/watermark_height))
        print(new_watermark_width, new_watermark_height)
        watermark_image = watermark_image.resize((new_watermark_width, new_watermark_height))
    else:
        new_watermark_width = int(src_width/3)
        new_watermark_height = int(new_watermark_width * (watermark_height/watermark_width))
        print(new_watermark_width, new_watermark_height)
        watermark_image = watermark_image.resize((new_watermark_width, new_watermark_height))

    # Calculate the position for the watermark image to be centered in the source image
    left = int((src_width - new_watermark_width) / 2)
    top = int((src_height - new_watermark_height) / 2)
    right = left + new_watermark_width
    bottom = top + new_watermark_height

    # Blend the source and watermark images
    #src_image = Image.blend(src_image, watermark_image, alpha=0.5)
    src_image.paste(watermark_image, (left, top, right, bottom), watermark_image)

    # Save the blended image to disk with the same format as the original image
    #image_extension = os.path.splitext(src_image_path)[1]
    src_image.save(src_image_path)
