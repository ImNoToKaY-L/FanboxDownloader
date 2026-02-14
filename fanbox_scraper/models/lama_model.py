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

    def __init__(self, device: str = 'cpu', model_path: Optional[str] = None):
        """
        Initialize LaMa model.

        Args:
            device: Device to use (cuda, mps, cpu)
            model_path: Path to model weights (if None, uses default)
        """
        self.device = device
        self.model_path = model_path
        self.model = None
        self.logger = logging.getLogger(__name__)

    def load_model(self):
        """
        Load the LaMa model with proper CPU/CUDA handling.
        """
        if self.model is not None:
            return

        try:
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
                    import os
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
            # Convert PIL images to numpy arrays
            image_np = np.array(image)
            mask_np = np.array(mask.convert('L'))

            # Ensure mask is binary
            mask_np = (mask_np > 127).astype(np.uint8) * 255

            # Run inpainting
            result_np = self.model(image_np, mask_np)

            # Convert back to PIL
            result = Image.fromarray(result_np)

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
