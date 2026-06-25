from tqdm import tqdm
import os
from pathlib import Path
import math
import numpy as np
import zipfile
from PIL import Image
import cv2
import shutil
import nd2

def grayscale(image):
    if len(image.shape) == 3 and image.shape[2] >= 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image

def OpenZip(fname):
    images = {}
    total_size = 0

    with zipfile.ZipFile(fname, 'r') as z:
        for fname in z.infolist():
            if fname.filename.endswith('.jpg'):
                print(fname.filename)
                with z.open(fname.filename) as file:
                    img = Image.open(file)
                    print(1)
                    img = Image.open(file).convert("RGB")
                    print(2)
                    img = np.array(Image.open(file).convert("RGB"))
                    print(3)
                    img = np.array(Image.open(file).convert("RGB"))[:, :, ::-1]
                    print(4)
                    print("checking filesize")
                    total_size += math.prod(img.shape)
                    images[int(Path(fname.filename).stem)] = img
                    print("setting dictionary")
    
    return images, total_size

def nd2_converter(filename, compression):
    filename = Path(filename)
    img_stack = nd2.imread(filename) 
    print(f"File shape: {img_stack.shape}")

    new_folder_name = filename.with_suffix('')
    os.makedirs(new_folder_name, exist_ok=True)
    pbar = tqdm(enumerate(img_stack), desc="Converting images to jpeg")
    for slice,arr in pbar:
        pbar.set_postfix_str(f"Current: {slice}")
        greyscale = grayscale(arr)
        cv2.imwrite(new_folder_name / f"{slice+1}.jpg", greyscale, [int(cv2.IMWRITE_JPEG_QUALITY), compression])

    print("Zipping images...")
    shutil.make_archive(new_folder_name, 'zip', new_folder_name)
    shutil.rmtree(new_folder_name)