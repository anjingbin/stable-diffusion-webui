import os
import sys
import traceback

import tensorflow as tf
import cv2
import numpy

#from nsfw_detector import predict
from modules import predict
from modules import paths, shared, devices, modelloader
from keras.optimizers import SGD

model_dir = "nsfw"
user_path = None
#model_name = "mobilenet_v2_140_224"
watermark_image= "nsfw-wm.png"
#model_name = "nsfw_mobilenet2.224x224.h5"
model_name = "nsfw.299x299.h5"
model_path = os.path.join(paths.models_path, model_dir, model_name)
watermark_image_path = os.path.join(paths.models_path, model_dir, watermark_image)
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
                [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=(1024))])
        except RuntimeError as e:
            print(e)

    model = predict.load_model(model_path)
    optim = SGD()
    model.compile(loss='categorical_crossentropy', optimizer=optim, metrics=['accuracy'])
    
    loaded_gfpgan_model = model

    # Load the watermark image
    if watermark is None:
        watermark = cv2.imread(watermark_image_path, cv2.IMREAD_UNCHANGED)

    return model


def nsfw_detect(image_path):
    model = nsfw()
    if model is None:
        return False 

    result = predict.classify(model,image_path, 299)
    inner_dict = result[image_path]
    if inner_dict.get('porn') > 0.8 or inner_dict.get('hentai') > 0.8:
        print('nsfw detected:', result)
        return True
    else:
        return False

def nsfw_detect_blur(image_path):
    if nsfw_detect(image_path):
        #print('blur image file:', image_path)
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


def nsfw_detect2(image):
    from PIL import Image
    from tensorflow.keras.utils import img_to_array
    model = nsfw()
    if model is None:
        return False

    #image = image.resize((299,299))
    img_array = img_to_array(image)
    print('image shape: ', img_array.shape)

    img_array = img_array.reshape((1,) + img_array.shape)

    print('image reshaped: ', img_array.shape)

    result = predict.classify_nd(model,img_array)
    print('detect result: ', result)
    inner_dict = result[0]
    print(result)
    if inner_dict.get('porn') > 0.8 or inner_dict.get('hentai') > 0.8:
        print('nsfw detected.')
        return True
    else:
        return False
