# pixi run time python -u src/counter.py > outs/counter.out 2>&1
# pixi run python -m memray run -o outs/output.bin src/counter.py
# pixi run python -m memray flamegraph outs/output.bin

from pathlib import Path
import tracemalloc

import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from tqdm import tqdm

import cv2
from skimage.feature import blob_doh
from sklearn.cluster import DBSCAN

import session_info
session_info.show()
tracemalloc.start()

# Ins/Outs
DATA_DIRECTORY = Path(".") / "data"
INPUT_FILE = "test_image.jpg"
INPUT = DATA_DIRECTORY / INPUT_FILE
IMAGE_SPLITBY = 2 

OUTPUT_DIRECTORY = Path(".") / "plot"
IMAGE_NAME = "test-choano-classification"
OUTPUT = OUTPUT_DIRECTORY / f"{IMAGE_NAME}.jpg"

""" 1 to process whole image, 2 to create 2x2 grid """

"""
Choose your mode:

MODE 1: direct cleaning
- halo subtraction (Opening to get halo, then subtract it out)
- blur
- normalization & greyscale

MODE 2: convert to dot
- create halo (Opening [keep only major outlines, then stich together] to get halo)
- fill halo (Closing [expand existing outlines, then shrink to make discrete] to fill halo)
- normalization & greyscale
- enhance contrast (local/adaptive normalization)
"""
MODE = 2

# Image Preprocessing
HALO_KERNEL_1 = 20
HALO_KERNEL_2 = 20

BLUR_SIZE = 25
""" Must be odd """
BLUR_STD = 5

CONTRAST = 2.0
CONTRAST_TILES = 5

# Blob Identification
SIZE_MIN = 14
SIZE_MAX = 25
SIZE_RANGE = 8
""" how many size circles to test, with overlapping circles removed """
QUALITY_THRESHOLD = 0.0005
""" Default 0.0009 for MODE 2 """
MAX_OVERLAP = 0.3
""" Default 0.35 for MODE 2 """

# Clustering Identification
CLUSTER_MIN = 4
EPS = 80


if __name__ == "__main__":
    full_img = cv2.imread(INPUT)

    # cut images
    M = full_img.shape[0]//(IMAGE_SPLITBY)
    N = full_img.shape[1]//(IMAGE_SPLITBY)
    tiles = [full_img[x-M:x,y-N:y]
                for x in range(M,full_img.shape[0]+1,M)
                for y in range(N,full_img.shape[1]+1,N)]
    
    total_counter = {
        "isolated" : 0,
        "clumped" : 0,
        "clumps" : 0
    }

    # plotting object
    f, axs = plt.subplots(IMAGE_SPLITBY, IMAGE_SPLITBY, figsize=(8*IMAGE_SPLITBY, 8*IMAGE_SPLITBY), layout="constrained")
    if type(axs) == np.ndarray: axs = axs.flatten()

    for t,img in tqdm(enumerate(tiles), desc="Processing image tiles", total=len(tiles)):
        if MODE == 1: # direct clean
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (HALO_KERNEL_1, HALO_KERNEL_2))
            bg_halo = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel) # find circles
            cleaned_img = cv2.subtract(img, bg_halo) # remove circles to remove halo
            cleaned_img = cv2.GaussianBlur(cleaned_img, (BLUR_SIZE, BLUR_SIZE), BLUR_STD) # blur insides
            cleaned_img = cv2.normalize(cleaned_img, None, 50, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U) # normalize
            cleaned_img = cv2.cvtColor(cleaned_img, cv2.COLOR_BGR2GRAY) # grayscale

            blobs = blob_doh(
                cleaned_img,
                min_sigma=SIZE_MIN,
                max_sigma=SIZE_MAX,
                num_sigma=SIZE_RANGE,
                threshold=QUALITY_THRESHOLD,
                overlap=MAX_OVERLAP,
            )

            blobs[:, 2] = blobs[:, 2] * np.sqrt(2)
            xy = blobs[:, :2]

        elif MODE == 2: # generate dots
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (HALO_KERNEL_1, HALO_KERNEL_2))
            cleaned_img = cv2.morphologyEx(img, cv2.MORPH_OPEN, kernel) # fill once
            cleaned_img = cv2.morphologyEx(cleaned_img, cv2.MORPH_CLOSE, kernel) # fill opposite way
            cleaned_img = cv2.normalize(cleaned_img, None, 50, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U) # normalize
            cleaned_img = cv2.cvtColor(cleaned_img, cv2.COLOR_BGR2GRAY) # grayscale
            clahe = cv2.createCLAHE(clipLimit=CONTRAST,tileGridSize=(CONTRAST_TILES,CONTRAST_TILES))
            cleaned_img = clahe.apply(cleaned_img)

            blobs = blob_doh(
                cleaned_img,
                min_sigma=SIZE_MIN,
                max_sigma=SIZE_MAX,
                num_sigma=SIZE_RANGE,
                threshold=QUALITY_THRESHOLD,
                overlap=MAX_OVERLAP,
            )

            blobs[:, 2] = blobs[:, 2] * np.sqrt(2)
            xy = blobs[:, :2]
        
        else:
            raise ValueError("Valid MODE options: [ 1, 2 ]")

        # identify & count clusters
        cluster_ids = DBSCAN(
            eps=EPS,
            min_samples=1,
            n_jobs=-1,
        ).fit_predict(xy)
        cluster_sizes = Counter(cluster_ids)
        isolated = sum(s for s in cluster_sizes.values() if s < CLUSTER_MIN)
        clumped  = sum(s for s in cluster_sizes.values() if s >= CLUSTER_MIN)
        clumps   = sum(1 for s in cluster_sizes.values() if s >= CLUSTER_MIN)
        total_counter["isolated"] += isolated
        total_counter["clumped"] += clumped
        total_counter["clumps"] += clumps
        print(
            f"-- Tile {t} --\n\
            Isolated: {isolated}\n\
            Clumped: {clumped}\n\
            Clumps: {clumps}")

        # image
        axs[t].imshow(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cmap="gray")
        for i, (y, x, radius) in enumerate(blobs):
            size = cluster_sizes[cluster_ids[i]]
            color = "red" if size >= CLUSTER_MIN else "blue"
            axs[t].add_patch(
                plt.Circle(
                    (x, y),
                    radius/2,
                    color=color,
                    fill=True,
                    linewidth=0.7,
                )
            )
        axs[t].axis("off")

    print(
        f"-------- TOTAL {t} --------\n\
        Isolated: {total_counter["isolated"]}\n\
        Clumped: {total_counter["clumped"]}\n\
        Clumps: {total_counter["clumps"]}")
    f.suptitle(f"$Automatic Choano Counting$\nIsolated: {total_counter["isolated"]} & Clumped: {total_counter["clumped"]} ({total_counter["clumps"]})")

    f.savefig(OUTPUT_DIRECTORY / f"{IMAGE_NAME}.jpg", dpi=800)

    # Retrieve (current_usage, peak_usage) in bytes
    _, peak = tracemalloc.get_traced_memory()
    print(f"Peak Memory Usage: {peak / 10**6:.2f} MB / {peak / 10**9:.2f} GB")
    tracemalloc.stop()