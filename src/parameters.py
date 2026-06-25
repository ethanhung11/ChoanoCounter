from dataclasses import dataclass, field
import os

@dataclass
class Parameters:

    mode: int = field(
        default=2,
        metadata={
            "min": 1,
            "max": 2,
            "step": 1,
            "label": "Mode",
            "section": "Image Processing",
            "detail" : "Mode 1: \n \
                        Mode 2:",
        }
    )

    image_splitby: int = field(
        default=1,
        metadata={
            "min": 1,
            "max": 8,
            "step": 1,
            "label": "Image Tiling",
            "section": "Image Processing",
            "detail" : f"""Splits the image into equally sized (e.g. "2" creates 4 tiles in 2x2 arrangement). This can decrease runtime by [ min(cores, tiles) / tiles ], at the cost of border artifacts.\nYou have {os.cpu_count()} cores.""",
        }
    )
    

    halo_kernel_1: int = field(
        default=15,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Halo Kernel (x)",
            "section": "Image Processing",
            "detail" : """The width of the elipse kernel. Larger values suppress noise/illumination artifact (like halos) but can erase clumped/small objects.""",
        }
    )

    halo_kernel_2: int = field(
        default=15,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Halo Kernel (y)",
            "section": "Image Processing",
            "detail" : """The height of the ellipse kernel. Larger values are better able to remove illumination artifact (like halos), but can merged clumped objects and erase small cells.""",
        }
    )

    blur_size: int = field(
        default=5,
        metadata={
            "min": 1,
            "max": 65,
            "step": 2,
            "label": "Blur Size",
            "section": "Image Processing",
            "detail" : """The kernel size for Gaussian blur. Larger values consider pixels further away in the blurring. Must be odd as the center pixel must be centered (e.g. 1, 2, 3 px in all directions)""",
        }
    )

    blur_std: int = field(
        default=1,
        metadata={
            "min": 1.0,
            "max": 30.0,
            "step": 0.1,
            "label": "Blur σ",
            "section": "Image Processing",
            "detail" :  """The standard deviation for Gaussian blur. Larger values smooth the image more to remove noise but weaken sharp boundaries.""",
        }
    )

    contrast_threshold: float = field(
        default=1,
        metadata={
            "min": 1,
            "max": 10,
            "step": 1,
            "label": "Contrast Threshold",
            "section": "Image Processing",
            "detail" : """The CLAHE contrast clip limit. Lower values lead to aggressive contrast. Contrast helps identify faint objects but can amplify noise.""",
        }
    )

    contrast_tiles: int = field(
        default=5,
        metadata={
            "min": 1,
            "max": 40,
            "step": 1,
            "label": "Contrast Tiles",
            "section": "Image Processing",
            "detail" : """The number of tile splits CLAHE uses, per dimension. More tiles leads to more local contrast adjustment.""",
        }
    )

    size_min: int = field(
        default=15,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Blob Min",
            "section": "Object Identification",
            "detail" : "",
        }
    )

    size_max: int = field(
        default=30,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Blob Max",
            "section": "Object Identification",
            "detail" : "",
        }
    )

    size_steps: int = field(
        default=3,
        metadata={
            "min": 1,
            "max": 20,
            "step": 1,
            "label": "Blob Steps",
            "section": "Object Identification",
            "detail" : """The number size steps to check for blobs between min/max range. Larger values improves identification at different size scales, but is slower and can increase false detections.""",
        }
    )

    quality_threshold: float = field(
        default=0.0040,
        metadata={
            "min": 0.0001,
            "max": 0.0100,
            "step": 0.0001,
            "label": "Blob Quality Threshold",
            "section": "Object Identification",
            "detail" : """The parameter controlling the quality of the blob identification. Larger values leave only the most distinct blobs, but may ignore faint or oddly shaped cells.""",
        }
    )

    max_overlap: float = field(
        default=0.6,
        metadata={
            "min": 0.01,
            "max": 1.00,
            "step": 0.01,
            "label": "Blob Max Overlap",
            "section": "Object Identification",
            "detail" : """The maximum overlap two identified blobs can have before the smaller one is erased. Smaller values identify true cells better but significantly increase duplication errors of singlets.""",
        }
    )

    cluster_min: float = field(
        default=4,
        metadata={
            "min": 2,
            "max": 6,
            "step": 1,
            "label": "Cluster Group Minimum",
            "section": "Object Identification",
            "detail" : """Defaults to 4 for rosettes. Available for testing.""",
        }
    )

    eps: float = field(
        default=80,
        metadata={
            "min": 1,
            "max": 160,
            "step": 1,
            "label": "Cluster Range",
            "section": "Object Identification",
            "detail" : """DBSCAN's epsilon (ε), corresponding to the maximum radius to consider clumps. Smaller values group more discriminately but suffer if clump identification is poor.""",
        }
    )

    circle_thickness: int = field(
        default=5,
        metadata={
            "min": 1,
            "max": 15,
            "step": 1,
            "label": "Output Label Thickness",
            "section": "Output Settings",
            "detail" : """Thickness of the colored circles identifying cells in the output image.""",
        }
    )