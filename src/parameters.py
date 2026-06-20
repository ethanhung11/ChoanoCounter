from dataclasses import dataclass, field

@dataclass
class Parameters:

    mode: int = field(
        default=2,
        metadata={
            "min": 1,
            "max": 2,
            "step": 1,
            "label": "Mode",
            "section": "Image Processing"
        }
    )

    image_splitby: int = field(
        default=1,
        metadata={
            "min": 1,
            "max": 5,
            "step": 1,
            "label": "Image Tiling",
            "section": "Image Processing"
        }
    )
    

    halo_kernel_1: int = field(
        default=20,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Halo Kernel (x)",
            "section": "Image Processing"
        }
    )

    halo_kernel_2: int = field(
        default=20,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Halo Kernel (y)",
            "section": "Image Processing"
        }
    )

    blur_size: int = field(
        default=25,
        metadata={
            "min": 1,
            "max": 65,
            "step": 2,
            "label": "Blur Size",
            "section": "Image Processing"
        }
    )

    blur_std: int = field(
        default=5,
        metadata={
            "min": 1.0,
            "max": 30.0,
            "step": 0.1,
            "label": "Blur σ",
            "section": "Image Processing"
        }
    )

    contrast_threshold: float = field(
        default=2,
        metadata={
            "min": 1,
            "max": 10,
            "step": 1,
            "label": "Contrast Threshold",
            "section": "Image Processing"
        }
    )

    contrast_tiles: int = field(
        default=5,
        metadata={
            "min": 1,
            "max": 40,
            "step": 1,
            "label": "Contrast Tiles",
            "section": "Image Processing"
        }
    )

    size_min: int = field(
        default=14,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Size Min",
            "section": "Object Identification",
        }
    )

    size_max: int = field(
        default=25,
        metadata={
            "min": 1,
            "max": 50,
            "step": 1,
            "label": "Size Max",
            "section": "Object Identification",
        }
    )

    size_steps: int = field(
        default=8,
        metadata={
            "min": 1,
            "max": 20,
            "step": 1,
            "label": "Size Steps",
            "section": "Object Identification",
        }
    )

    quality_threshold: float = field(
        default=0.0009,
        metadata={
            "min": 0.0001,
            "max": 0.0100,
            "step": 0.0001,
            "label": "Quality Threshold",
            "section": "Object Identification",
        }
    )

    max_overlap: float = field(
        default=0.35,
        metadata={
            "min": 0.01,
            "max": 1.00,
            "step": 0.01,
            "label": "Max Overlap",
            "section": "Object Identification",
        }
    )

    cluster_min: float = field(
        default=4,
        metadata={
            "min": 2,
            "max": 6,
            "step": 1,
            "label": "Group Threshold",
            "section": "Object Identification",
        }
    )

    eps: float = field(
        default=80,
        metadata={
            "min": 1,
            "max": 160,
            "step": 1,
            "label": "DBSCAN Epsilon (ε)",
            "section": "Object Identification",
        }
    )

    circle_thickness: int = field(
        default=3,
        metadata={
            "min": 1,
            "max": 15,
            "step": 1,
            "label": "Output Label Thickness",
            "section": "Output Settings",
        }
    )