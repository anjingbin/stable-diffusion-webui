import os
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
                    # 根据scene和suggestion设置后续操作。
                    # 根据不同的suggestion结果做业务上的不同处理。例如，将违规数据删除等。
                    print(suggestion)
                    print(scene)
                    if suggestion == "block":
                        return True
    return False
                
    # if 200 == result["code"]:
    #     taskResults = result["data"]
    #     for taskResult in taskResults:
    #         if(200 == taskResult["code"]):
    #             taskId = taskResult["taskId"]
    #             # 保存taskId。间隔一段时间后使用taskId查询检测结果。
    #             print(taskId)

def nsfw_detect_blur(image_path):
    if nsfw_detect(image_path):
        print('blur image file:', image_path)
        src = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        dst = cv2.GaussianBlur(src,(51,51),50)
       
        #watermarking
        if watermark is not None:

            # Get the dimensions of the original image
            h, w, _ = dst.shape

            # Get the dimensions of the watermark image
            hw, ww, _ = watermark.shape

            # Calculate the center coordinates of the original image
            center_y = int(h/2)
            center_x = int(w/2)

            # Calculate the top left corner coordinates of the watermark image
            top_y = center_y - int(hw/2)
            top_x = center_x - int(ww/2)

            # Get the alpha channel of the watermark image
            watermark_alpha = watermark[:,:,3]

            # Create a mask of the watermark alpha channel
            mask = cv2.merge((watermark_alpha, watermark_alpha, watermark_alpha))

            # Copy the watermark image to the center of the original image using the mask
            dst[top_y:top_y+hw, top_x:top_x+ww] = cv2.multiply(mask/255, watermark[:,:,:3]/255) * 255 + cv2.multiply(1 - mask/255, dst[top_y:top_y+hw, top_x:top_x+ww]/255) * 255

        cv2.imwrite(image_path,dst)

