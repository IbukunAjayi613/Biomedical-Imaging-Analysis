import numpy as np
import matplotlib.pyplot as plt

from scipy.ndimage import gaussian_filter, sobel, label, center_of_mass
from pathlib import Path


def convert2gray(image):

    rgb_image = image[:,:, :3]

    gray_image = (
        .299 * rgb_image[:,:,0]+
        .587 * rgb_image[:,:,1]+
        .114 * rgb_image[:,:,2]
    )

    return gray_image

def applysmoothing(image, sigma):

    smoothed = gaussian_filter(image, sigma = sigma)

    return smoothed

def detectedge(image):
    edx = sobel(image, axis=1)
    edy = sobel(image, axis=0)

    edges = np.sqrt(edx**2 + edy**2)

    max_edge = np.max(edges)

    if max_edge > 0:
        norm_edge = edges / max_edge

    else:
        norm_edge = np.zeros_like(edges)

    return norm_edge

def segment(image, threshold):

    mask = image > threshold

    return mask

def analyzeR(mask, min_area):

    labelimage, numf = label(mask)
    region = np.bincount(labelimage.ravel())
    kept_region = np.where(region >= min_area)[0]
    kept_region = kept_region[kept_region !=0]

    return labelimage, numf, region, kept_region

def calcentroids(mask, labelimage, kept_region):

    if len(kept_region) == 0:
        return []

    centroids = center_of_mass(mask, labels=labelimage, index=kept_region)
    return centroids

def visualRes(rgb_image, gray_image, smoothed, edges, segment_mask, centroids, kept_region, outpath):

    fig, axes = plt.subplots(2, 3, figsize=(14,9))

    axes[0, 0].imshow(rgb_image)
    axes[0, 0].set_title("Original Image")

    axes[0, 1].imshow(gray_image, cmap="gray", vmin=0, vmax=1)
    axes[0, 1].set_title("Grayscale")

    axes[0, 2].imshow(smoothed, cmap="gray", vmin=0, vmax=1)
    axes[0, 2].set_title("Gaussian Smoothing")

    axes[1, 0].imshow(edges, cmap="gray", vmin=0, vmax=1)
    axes[1, 0].set_title("Sobel Edge Detection")

    axes[1, 1].imshow(segment_mask, cmap="gray")
    axes[1, 1].set_title("Segmentation Mask")

    axes[1, 2].imshow(segment_mask, cmap="gray")

    for i, region_id in enumerate(kept_region):

        center_row, center_col = centroids[i]

        axes[1,2].plot(center_col, center_row, "ro", markersize=5)

        axes[1,2].text(center_col + 10, center_row, str(region_id), color="yellow", fontsize=8)
    
    axes[1,2].set_title("Regions centroids")

    for ax in axes.flat:
        ax.axis("off")

    plt.tight_layout()

    plt.savefig(outpath, dpi=150, bbox_inches="tight")

    plt.show() 

    plt.close(fig)


def main():

    sigma = 1
    threshold = .2
    min_area = 25


    script_dir = Path(__file__).resolve().parent

    image_path = script_dir / "sample.png"


    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    image = plt.imread(image_path)

    if image.ndim != 3 or image.shape[2] not in (3, 4):
        raise ValueError("Expected an RGB or RGBA image.")

    if image.dtype == np.uint8:
        image = image.astype(np.float32) / 255.0

    elif not np.issubdtype(image.dtype, np.floating):
        raise TypeError("Unsupported image data type.")

    if not np.all(np.isfinite(image)):
        raise ValueError("Image contains invalid pixel values.")

    if np.min(image) < 0 or np.max(image) > 1:
        raise ValueError("Expected pixel intensities between 0 and 1.")


    gray_image = convert2gray(image)

    smoothed = applysmoothing(gray_image, sigma)

    edges = detectedge(smoothed)

    segment_mask = segment(smoothed, threshold)

    labelimage, numf, region, kept_region = analyzeR(segment_mask, min_area)

    centroids = calcentroids(segment_mask, labelimage, kept_region)

    results_dir = script_dir / "results"
    results_dir.mkdir(exist_ok=True)

    outpath = results_dir / "functional_pipeline.png"

    visualRes(image[:,:,:3], gray_image, smoothed, edges, segment_mask, centroids, kept_region, outpath)


    for i, region_id in enumerate(kept_region):

        area = region[region_id]
        center_row, center_col = centroids[i]

        print(f"Region {region_id}: Area = {area} pixels, Centroid = ({center_row:.1f}, {center_col:.1f})")


    print("BIOMEDICAL IMAGING ANALYSIS")
    print("---------------------------")

    print("Gaussian Sigma:", sigma)
    print("Segment Threshold:", threshold)
    print("Minimum region area:", min_area)

    print("Total connected regions:", numf)
    print("Qualifying regions:", len(kept_region))

    print()
    print("Analysis saved to:", outpath)
    print("File exists:", outpath.exists())

if __name__ == "__main__":
     main()
