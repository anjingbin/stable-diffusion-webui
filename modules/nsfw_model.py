import os
import sys
import traceback

import tensorflow as tf
import cv2
import numpy

from nsfw_detector import predict
from modules import paths, shared, devices, modelloader

model_dir = "nsfw"
user_path = None
#model_name = "mobilenet_v2_140_224"
watermark_image= "nsfw-wm.png"
model_name = "nsfw_mobilenet2.224x224.h5"
model_path = os.path.join(paths.models_path, model_dir, model_name)
watermark_image_path = os.path.join(paths.models_path, model_dir, watermark_image)
model_url = "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.0/GFPGANv1.4.pth"
loaded_nsfw_model= None
watermark = None

def nsfw():
    global loaded_nsfw_model
    global model_path
    global watermark

    if loaded_nsfw_model is not None:
        return loaded_nsfw_model

    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            # Restrict TensorFlow to only allocate X GB of memory on the first GPU (use less memory if you have multiple GPUs)
            tf.config.experimental.set_virtual_device_configuration(
                gpus[0],
                [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=(256))])
        except RuntimeError as e:
            print(e)

    model = predict.load_model(model_path)
    loaded_gfpgan_model = model

    # Load the watermark image
    if watermark is None:
        watermark = cv2.imread(watermark_image_path, cv2.IMREAD_UNCHANGED)

    return model


def nsfw_detect(image_path):
    model = nsfw()
    if model is None:
        return False 

    result = predict.classify(model,image_path)
    inner_dict = result[image_path]
    print(result)
    if inner_dict.get('porn') > 0.8 or inner_dict.get('hentai') > 0.8:
        print('nsfw detected.')
        return True
    else:
        return False

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


