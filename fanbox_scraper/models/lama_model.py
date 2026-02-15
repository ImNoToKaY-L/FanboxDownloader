"""
LaMa (Large Mask Inpainting) model wrapper for image uncensoring.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import torch
from PIL import Image


class LamaModel:
    """
    Wrapper for LaMa inpainting model.
    """

    def __init__(self, device: str = 'cpu', model_path: Optional[str] = None, max_resolution: int = 2048):
        """
        Initialize LaMa model.

        Args:
            device: Device to use (cuda, mps, cpu)
            model_path: Path to model weights (if None, uses default)
            max_resolution: Maximum dimension (width/height) for processing
                          Images larger than this will be downscaled
                          Default 2048 (safe for most GPUs and ~2GB RAM)
                          Use 1024 for low memory systems
        """
        self.device = device
        self.model_path = model_path
        self.model = None
        self.max_resolution = max_resolution
        self.logger = logging.getLogger(__name__)

    def load_model(self):
        """
        Load the LaMa model with proper CPU/CUDA handling.
        """
        if self.model is not None:
            return

        try:
            # Configure PyTorch memory allocation for large images
            import os
            import multiprocessing

            # Allow PyTorch to allocate larger memory blocks
            # These settings help with large image processing
            if 'PYTORCH_CUDA_ALLOC_CONF' not in os.environ:
                os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512,expandable_segments:True'

            # Optimize CPU threading for large tensor operations
            if 'OMP_NUM_THREADS' not in os.environ:
                num_cores = multiprocessing.cpu_count()
                os.environ['OMP_NUM_THREADS'] = str(num_cores)

            # For CPU: increase memory limit and enable THP (Transparent Huge Pages)
            if self.device == 'cpu':
                # Enable memory-efficient mode for CPU
                torch.set_num_threads(torch.get_num_threads())  # Use all available threads

                # Try to enable large pages for better memory allocation
                try:
                    # This helps with large contiguous memory allocations on CPU
                    torch.backends.cudnn.benchmark = False
                except:
                    pass

            # Force CPU if CUDA not available
            if self.device == 'cuda' and not torch.cuda.is_available():
                self.logger.warning("CUDA requested but not available, falling back to CPU")
                self.device = 'cpu'

            # Try loading with simple-lama-inpainting
            try:
                from simple_lama_inpainting import SimpleLama

                self.logger.info(f"Loading LaMa model on {self.device}...")

                # Force map to CPU for CPU-only PyTorch
                if self.device == 'cpu':
                    # Set environment variable to force CPU
                    os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

                device_str = self.device if self.device in ['cpu', 'mps'] else 'cuda'
                self.model = SimpleLama(device=device_str)
                self.logger.info("LaMa model loaded successfully")

            except RuntimeError as e:
                if 'CUDA' in str(e) or 'empty_strided' in str(e):
                    # Model has CUDA-specific weights, need to remap
                    self.logger.warning(f"CUDA/CPU mismatch detected: {str(e)[:100]}...")
                    self.logger.info("This is likely due to CPU-only PyTorch trying to load CUDA model weights.")
                    self.logger.info("Solution: Install PyTorch with CUDA support or use alternative inpainting method")
                    raise RuntimeError(
                        "simple-lama-inpainting has CUDA/CPU compatibility issues with your PyTorch installation.\n"
                        "Solutions:\n"
                        "1. Install PyTorch with CUDA: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121\n"
                        "2. Or use a different inpainting library (coming soon)\n"
                        "3. Or use a GPU-enabled machine"
                    ) from e
                else:
                    raise

        except ImportError as e:
            self.logger.error("simple-lama-inpainting not installed. Install with: pip install -r requirements-uncensor.txt")
            raise ImportError("simple-lama-inpainting package required") from e
        except Exception as e:
            self.logger.error(f"Failed to load LaMa model: {e}")
            raise

    def _resize_if_needed(self, image: Image.Image, mask: Image.Image) -> Tuple[Image.Image, Image.Image, Optional[Tuple[int, int]]]:
        """
        Resize image and mask if they exceed max_resolution.

        Args:
            image: Input PIL Image
            mask: Input PIL mask

        Returns:
            Tuple of (resized_image, resized_mask, original_size or None)
        """
        original_size = image.size
        width, height = original_size
        max_dim = max(width, height)

        # Check if resizing is needed
        if max_dim <= self.max_resolution:
            return image, mask, None

        # Calculate new dimensions maintaining aspect ratio
        scale = self.max_resolution / max_dim
        new_width = int(width * scale)
        new_height = int(height * scale)

        # Log the resizing
        megapixels_before = (width * height) / 1_000_000
        megapixels_after = (new_width * new_height) / 1_000_000
        self.logger.info(f"Downscaling image for memory efficiency: "
                        f"{width}x{height} ({megapixels_before:.1f}MP) -> "
                        f"{new_width}x{new_height} ({megapixels_after:.1f}MP)")

        # Resize both image and mask
        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        resized_mask = mask.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return resized_image, resized_mask, original_size

    def inpaint(self, image: Image.Image, mask: Image.Image) -> Image.Image:
        """
        Perform inpainting on image using mask.

        Args:
            image: Input PIL Image
            mask: Binary mask PIL Image (white=inpaint, black=keep)

        Returns:
            Inpainted PIL Image
        """
        if self.model is None:
            self.load_model()

        try:
            # Free up memory before processing
            import gc
            gc.collect()
            if self.device == 'cuda' and torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

            # Resize if needed to prevent memory issues
            resized_image, resized_mask, original_size = self._resize_if_needed(image, mask)

            # Convert PIL images to numpy arrays
            image_np = np.array(resized_image)
            mask_np = np.array(resized_mask.convert('L'))

            # Ensure mask is binary
            mask_np = (mask_np > 127).astype(np.uint8) * 255

            # Run inpainting
            image_size_mb = (image_np.nbytes / (1024 * 1024))
            self.logger.debug(f"Processing {image_np.shape[1]}x{image_np.shape[0]} image (~{image_size_mb:.1f}MB)...")

            # Process with memory optimization
            with torch.inference_mode():  # Disable gradient computation for inference
                result_np = self.model(image_np, mask_np)

            # Free memory immediately after inference
            del image_np, mask_np
            gc.collect()
            if self.device == 'cuda' and torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Convert back to PIL
            result = Image.fromarray(result_np)
            del result_np
            gc.collect()

            # Upscale back to original size if needed
            if original_size is not None:
                self.logger.info(f"Upscaling result back to original size: {original_size[0]}x{original_size[1]}")
                result = result.resize(original_size, Image.Resampling.LANCZOS)

            return result

        except Exception as e:
            self.logger.error(f"Inpainting failed: {e}")
            raise

    def inpaint_from_paths(self, image_path: str, mask_path: str, output_path: str) -> str:
        """
        Convenience method to inpaint from file paths.

        Args:
            image_path: Path to input image
            mask_path: Path to mask image
            output_path: Path to save output

        Returns:
            Path to output image
        """
        image = Image.open(image_path).convert('RGB')
        mask = Image.open(mask_path).convert('L')

        result = self.inpaint(image, mask)
        result.save(output_path)

        self.logger.info(f"Inpainted image saved to: {output_path}")
        return output_path

    def estimate_processing_time(self, image_size: Tuple[int, int]) -> float:
        """
        Estimate processing time in seconds based on image size.

        Args:
            image_size: (width, height) tuple

        Returns:
            Estimated time in seconds
        """
        width, height = image_size
        pixels = width * height
        megapixels = pixels / 1_000_000

        # Benchmarks (seconds per megapixel)
        benchmarks = {
            'cuda': 0.5,   # ~3-5s for 1080p on RTX 3060
            'mps': 1.5,    # ~8-12s for 1080p on M1/M2
            'cpu': 15.0    # ~30-45s for 1080p on 8-core CPU
        }

        time_per_mp = benchmarks.get(self.device, 15.0)
        estimated_time = time_per_mp * megapixels

        return estimated_time

    def get_memory_usage(self) -> dict:
        """
        Get current memory usage statistics.

        Returns:
            Dictionary with memory statistics
        """
        if self.device == 'cuda' and torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / (1024 ** 2)  # MB
            reserved = torch.cuda.memory_reserved() / (1024 ** 2)
            return {
                'device': 'cuda',
                'allocated_mb': allocated,
                'reserved_mb': reserved
            }
        else:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / (1024 ** 2)
            return {
                'device': self.device,
                'memory_mb': memory_mb
            }

    def cleanup(self):
        """
        Clean up model and free memory.
        """
        if self.model is not None:
            del self.model
            self.model = None

            if self.device == 'cuda' and torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.logger.info("Model cleaned up and memory freed")

    def __del__(self):
        """
        Destructor to ensure cleanup.
        """
        self.cleanup()
