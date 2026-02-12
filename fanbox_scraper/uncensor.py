"""
Image uncensoring module for removing mosaic/pixelation censorship.
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict
import numpy as np
from PIL import Image
import cv2

from .models.model_loader import ModelLoader
from .models.lama_model import LamaModel


class ImageUncensor:
    """
    Main class for uncensoring images with mosaic/pixelation censorship.
    """

    def __init__(
        self,
        device: str = 'cpu',
        model_type: str = 'lama',
        auto_detect: bool = True,
        output_dir: str = 'uncensored',
        cache_dir: str = 'models'
    ):
        """
        Initialize image uncensor.

        Args:
            device: Device to use (cuda, mps, cpu)
            model_type: Model to use (lama)
            auto_detect: Automatically detect censored areas
            output_dir: Directory to save uncensored images
            cache_dir: Directory for model cache
        """
        self.device = device
        self.model_type = model_type
        self.auto_detect = auto_detect
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.model_loader = ModelLoader(cache_dir=cache_dir)

        # Validate and set device
        self.device = self.model_loader.get_device(self.device)

        # Initialize model (lazy loading)
        self.model = None

    def _load_model(self):
        """
        Load the uncensoring model (lazy loading).
        """
        if self.model is not None:
            return

        if self.model_type == 'lama':
            self.model = LamaModel(device=self.device)
            self.model.load_model()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def detect_censorship(
        self,
        image: Image.Image,
        threshold: float = 0.7,
        min_area: int = 100
    ) -> Optional[Image.Image]:
        """
        Automatically detect censored areas in image.

        Args:
            image: Input PIL Image
            threshold: Detection confidence threshold (0-1)
            min_area: Minimum area of censored region in pixels

        Returns:
            Binary mask PIL Image or None if no censorship detected
        """
        try:
            # Convert to numpy for processing
            img_np = np.array(image.convert('RGB'))

            # Detect pixelation/mosaic using edge detection and frequency analysis
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

            # Method 1: Detect blocky patterns (mosaic)
            # Use Laplacian variance to detect low-detail areas
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            laplacian_var = cv2.blur(np.abs(laplacian), (15, 15))

            # Method 2: Detect sharp edges (blocky patterns)
            edges = cv2.Canny(gray, 50, 150)
            edge_density = cv2.blur(edges.astype(float) / 255, (15, 15))

            # Combine detection methods
            # Low variance + high edge density = likely mosaic
            mosaic_score = (edge_density > 0.3) & (laplacian_var < np.percentile(laplacian_var, 30))

            # Clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            mosaic_score = cv2.morphologyEx(mosaic_score.astype(np.uint8), cv2.MORPH_CLOSE, kernel)
            mosaic_score = cv2.morphologyEx(mosaic_score, cv2.MORPH_OPEN, kernel)

            # Find contours and filter by area
            contours, _ = cv2.findContours(mosaic_score, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Create final mask
            mask = np.zeros_like(gray)
            for contour in contours:
                area = cv2.contourArea(contour)
                if area >= min_area:
                    cv2.drawContours(mask, [contour], -1, 255, -1)

            # Expand mask slightly to ensure coverage
            kernel_expand = np.ones((10, 10), np.uint8)
            mask = cv2.dilate(mask, kernel_expand, iterations=2)

            if mask.sum() == 0:
                self.logger.info("No censorship detected")
                return None

            # Convert to PIL
            mask_pil = Image.fromarray(mask)
            self.logger.info(f"Detected censored area: {mask.sum() / 255} pixels")

            return mask_pil

        except Exception as e:
            self.logger.error(f"Censorship detection failed: {e}")
            return None

    def uncensor_image(
        self,
        image_path: str,
        mask_path: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Uncensor a single image.

        Args:
            image_path: Path to input image
            mask_path: Path to mask image (if None, auto-detect)
            output_path: Path to save output (if None, auto-generate)

        Returns:
            Path to uncensored image or None if failed
        """
        try:
            # Load model
            self._load_model()

            # Load image
            image = Image.open(image_path).convert('RGB')
            image_name = Path(image_path).stem
            image_ext = Path(image_path).suffix

            # Get or generate mask
            if mask_path:
                mask = Image.open(mask_path).convert('L')
                self.logger.info(f"Using provided mask: {mask_path}")
            elif self.auto_detect:
                self.logger.info("Auto-detecting censored areas...")
                mask = self.detect_censorship(image)
                if mask is None:
                    self.logger.warning("No censorship detected, skipping")
                    return None
            else:
                self.logger.error("No mask provided and auto-detect disabled")
                return None

            # Generate output path if not provided
            if output_path is None:
                output_path = self.output_dir / f"{image_name}_uncensored{image_ext}"
            else:
                output_path = Path(output_path)

            # Estimate processing time
            processing_time = self.model.estimate_processing_time(image.size)
            self.logger.info(f"Estimated processing time: {processing_time:.1f}s")

            # Perform uncensoring
            start_time = time.time()
            result = self.model.inpaint(image, mask)
            elapsed_time = time.time() - start_time

            # Save result
            result.save(output_path, quality=95)
            self.logger.info(f"Uncensored image saved: {output_path} (took {elapsed_time:.1f}s)")

            return str(output_path)

        except Exception as e:
            self.logger.error(f"Failed to uncensor {image_path}: {e}")
            return None

    def batch_uncensor(
        self,
        image_paths: List[str],
        mask_dir: Optional[str] = None,
        show_progress: bool = True
    ) -> Dict[str, List[str]]:
        """
        Uncensor multiple images.

        Args:
            image_paths: List of image paths
            mask_dir: Directory containing masks (if None, auto-detect)
            show_progress: Show progress bar

        Returns:
            Dictionary with 'success' and 'failed' lists
        """
        from tqdm import tqdm

        results = {
            'success': [],
            'failed': []
        }

        iterator = tqdm(image_paths, desc="Uncensoring images") if show_progress else image_paths

        for image_path in iterator:
            try:
                # Find corresponding mask if mask_dir provided
                mask_path = None
                if mask_dir:
                    image_name = Path(image_path).stem
                    mask_path = Path(mask_dir) / f"{image_name}_mask.png"
                    if not mask_path.exists():
                        mask_path = None

                # Uncensor
                output_path = self.uncensor_image(image_path, mask_path)

                if output_path:
                    results['success'].append(output_path)
                else:
                    results['failed'].append(image_path)

            except Exception as e:
                self.logger.error(f"Error processing {image_path}: {e}")
                results['failed'].append(image_path)

        self.logger.info(f"Batch complete: {len(results['success'])} success, {len(results['failed'])} failed")
        return results

    def get_stats(self) -> dict:
        """
        Get processing statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            'device': self.device,
            'model_type': self.model_type,
            'auto_detect': self.auto_detect,
            'output_dir': str(self.output_dir)
        }

        if self.model:
            stats['memory'] = self.model.get_memory_usage()

        cache_size = self.model_loader.get_cache_size()
        stats['cache_size_mb'] = cache_size

        return stats

    def cleanup(self):
        """
        Clean up resources and free memory.
        """
        if self.model:
            self.model.cleanup()
            self.model = None

    def __del__(self):
        """
        Destructor to ensure cleanup.
        """
        self.cleanup()
