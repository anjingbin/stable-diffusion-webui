from aliyunsdkcore import client
from aliyunsdkgreen.request.v20180509 import ImageSyncScanRequest,ImageAsyncScanRequest
from aliyunsdkcore.profile import region_provider
from aliyunsdkgreenextension.request.extension import ClientUploader
from aliyunsdkgreenextension.request.extension import HttpContentHelper

import json
import uuid

clt = client.AcsClient("LTAI5tKiMkrggjeEccezSE5a", "sW3p61ClU9McEtxgIScKiCvrIZZX36","cn-beijing")
region_provider.modify_point('Green', 'cn-beijing', 'green.cn-beijing.aliyuncs.com')

AccessKeyId = "LTAI5tKiMkrggjeEccezSE5a"

def nsfw_detect(image_path):

    # request = ImageAsyncScanRequest.ImageAsyncScanRequest()
    request = ImageSyncScanRequest.ImageSyncScanRequest()
    request.set_accept_format('JSON')

    uploader = ClientUploader.getImageClientUploader(clt)
    url = uploader.uploadFile(image_path)
    # url = "http://s7.bailusoft.com:7860/file=/opt/stable-diffusion-webui/outputs/txt2img-images/2023-04-13/00126-3328874972.png"

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
    # if 200 == result["code"]:
    #     taskResults = result["data"]
    #     for taskResult in taskResults:
    #         if(200 == taskResult["code"]):
    #             taskId = taskResult["taskId"]
    #             # 保存taskId。间隔一段时间后使用taskId查询检测结果。
    #             print(taskId)
    
nsfw_detect("/Users/anjingbin/Downloads/00034.jpg")