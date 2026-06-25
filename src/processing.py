import os
import numpy as np
from pathlib import Path
from collections import Counter
import shutil
import zipfile
import cv2
from PIL import Image
from skimage.feature import blob_doh
from sklearn.cluster import DBSCAN
from utils import grayscale

def process_image(
    image_or_path,
    params,
    progress_callback=None
):

    assert isinstance(image_or_path, str) or isinstance(image_or_path, np.ndarray)
    full_img = cv2.imread(str(image_or_path)) if isinstance(image_or_path, str) else image_or_path

    M = full_img.shape[0] // params.image_splitby
    N = full_img.shape[1] // params.image_splitby

    output = np.zeros_like(full_img)

    total_counter = {
        "isolated": 0,
        "clumped": 0,
        "clumps": 0,
    }

    tile_idx = 0
    total_tiles = params.image_splitby ** 2

    for row in range(params.image_splitby):

        for col in range(params.image_splitby):

            y0 = row * M
            y1 = (row + 1) * M

            x0 = col * N
            x1 = (col + 1) * N

            img = full_img[y0:y1, x0:x1]

            if params.mode == 1:

                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (
                        params.halo_kernel_1,
                        params.halo_kernel_2,
                    ),
                )

                bg_halo = cv2.morphologyEx(
                    img,
                    cv2.MORPH_OPEN,
                    kernel,
                )

                cleaned_img = cv2.subtract(
                    img,
                    bg_halo,
                )

                cleaned_img = cv2.GaussianBlur(
                    cleaned_img,
                    (
                        int(params.blur_size),
                        int(params.blur_size),
                    ),
                    params.blur_std,
                )

                cleaned_img = cv2.normalize(
                    cleaned_img,
                    None,
                    50,
                    255,
                    cv2.NORM_MINMAX,
                    dtype=cv2.CV_8U,
                )

                cleaned_img = grayscale(cleaned_img)

            elif params.mode == 2:

                kernel = cv2.getStructuringElement(
                    cv2.MORPH_ELLIPSE,
                    (
                        params.halo_kernel_1,
                        params.halo_kernel_2,
                    ),
                )

                cleaned_img = cv2.morphologyEx(
                    img,
                    cv2.MORPH_OPEN,
                    kernel,
                )

                cleaned_img = cv2.morphologyEx(
                    cleaned_img,
                    cv2.MORPH_CLOSE,
                    kernel,
                )

                cleaned_img = cv2.normalize(
                    cleaned_img,
                    None,
                    50,
                    255,
                    cv2.NORM_MINMAX,
                    dtype=cv2.CV_8U,
                )

                cleaned_img = grayscale(cleaned_img)

                clahe = cv2.createCLAHE(
                    clipLimit=params.contrast_threshold,
                    tileGridSize=(
                        int(params.contrast_tiles),
                        int(params.contrast_tiles),
                    ),
                )

                cleaned_img = clahe.apply(
                    cleaned_img
                )

            else:
                raise ValueError(
                    "Must be mode 1 or 2."
                )

            blobs = blob_doh(
                cleaned_img,
                min_sigma=int(params.size_min),
                max_sigma=int(params.size_max),
                num_sigma=int(params.size_steps),
                threshold=params.quality_threshold,
                overlap=params.max_overlap,
            )

            display_img = cv2.cvtColor(
                cleaned_img,
                cv2.COLOR_GRAY2BGR,
            )

            if len(blobs) > 0:

                blobs[:, 2] *= np.sqrt(2)

                xy = blobs[:, :2]

                cluster_ids = DBSCAN(
                    eps=params.eps,
                    min_samples=1,
                    n_jobs=-1,
                ).fit_predict(xy)

                cluster_sizes = Counter(
                    cluster_ids
                )

                isolated = sum(
                    s
                    for s in cluster_sizes.values()
                    if s < params.cluster_min
                )

                clumped = sum(
                    s
                    for s in cluster_sizes.values()
                    if s >= params.cluster_min
                )

                clumps = sum(
                    1
                    for s in cluster_sizes.values()
                    if s >= params.cluster_min
                )

                total_counter["isolated"] += isolated
                total_counter["clumped"] += clumped
                total_counter["clumps"] += clumps

                for i, (y, x, radius) in enumerate(blobs):

                    size = cluster_sizes[
                        cluster_ids[i]
                    ]

                    color = (
                        (0, 0, 255)
                        if size >= params.cluster_min
                        else (255, 0, 0)
                    )

                    cv2.circle(
                        full_img,
                        (
                            int(x),
                            int(y),
                        ),
                        int(radius / 2),
                        color,
                        thickness=params.circle_thickness,
                    )

            output[
                y0:y1,
                x0:x1,
            ] = full_img

            tile_idx += 1

            if progress_callback:
                progress_callback(
                    int(
                        100
                        * tile_idx
                        / total_tiles
                    )
                )

    return output, total_counter