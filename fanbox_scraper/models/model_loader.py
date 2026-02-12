"""
Model loader for downloading and caching AI models.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from tqdm import tqdm
import torch


class ModelLoader:
    """
    Handles downloading, caching, and loading of AI models.
    """

    def __init__(self, cache_dir: str = "models"):
        """
        Initialize model loader.

        Args:
            cache_dir: Directory to cache downloaded models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def get_device(self, preferred_device: Optional[str] = None) -> str:
        """
        Get the best available device for model inference.

        Args:
            preferred_device: Preferred device (cuda, mps, cpu)

        Returns:
            Available device string
        """
        if preferred_device == 'cuda' and torch.cuda.is_available():
            device = 'cuda'
            gpu_name = torch.cuda.get_device_name(0)
            self.logger.info(f"Using CUDA device: {gpu_name}")
        elif preferred_device == 'mps' and torch.backends.mps.is_available():
            device = 'mps'
            self.logger.info("Using MPS (Apple Silicon) device")
        else:
            device = 'cpu'
            if preferred_device and preferred_device != 'cpu':
                self.logger.warning(f"{preferred_device} not available, falling back to CPU")
            else:
                self.logger.info("Using CPU device")

        return device

    def download_from_url(self, url: str, filename: str, show_progress: bool = True) -> Path:
        """
        Download a file from URL with progress bar.

        Args:
            url: URL to download from
            filename: Filename to save as
            show_progress: Whether to show progress bar

        Returns:
            Path to downloaded file
        """
        import requests

        file_path = self.cache_dir / filename

        if file_path.exists():
            self.logger.info(f"Model already cached: {file_path}")
            return file_path

        self.logger.info(f"Downloading model from {url}")

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(file_path, 'wb') as f:
                if show_progress and total_size > 0:
                    with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))
                else:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            self.logger.info(f"Model downloaded successfully: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to download model: {e}")
            if file_path.exists():
                file_path.unlink()
            raise

    def download_from_huggingface(self, repo_id: str, filename: str) -> Path:
        """
        Download a model from Hugging Face Hub.

        Args:
            repo_id: Hugging Face repository ID
            filename: Filename in the repository

        Returns:
            Path to downloaded file
        """
        from huggingface_hub import hf_hub_download

        file_path = self.cache_dir / filename

        if file_path.exists():
            self.logger.info(f"Model already cached: {file_path}")
            return file_path

        self.logger.info(f"Downloading model from Hugging Face: {repo_id}/{filename}")

        try:
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=str(self.cache_dir)
            )

            # Copy to our cache directory for consistency
            import shutil
            shutil.copy(downloaded_path, file_path)

            self.logger.info(f"Model downloaded successfully: {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to download from Hugging Face: {e}")
            raise

    def get_cache_size(self) -> float:
        """
        Get total size of cached models in MB.

        Returns:
            Total size in megabytes
        """
        total_size = sum(
            f.stat().st_size
            for f in self.cache_dir.glob('**/*')
            if f.is_file()
        )
        return total_size / (1024 * 1024)

    def clear_cache(self):
        """
        Clear all cached models.
        """
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info("Model cache cleared")

    def estimate_memory_usage(self, device: str, model_type: str = 'lama') -> dict:
        """
        Estimate memory usage for model inference.

        Args:
            device: Device to use (cuda, mps, cpu)
            model_type: Type of model

        Returns:
            Dictionary with memory estimates
        """
        estimates = {
            'lama': {
                'cuda': {'model': 2048, 'inference': 2048},  # MB
                'mps': {'model': 2048, 'inference': 2048},
                'cpu': {'model': 1024, 'inference': 4096}
            }
        }

        return estimates.get(model_type, {}).get(device, {'model': 1024, 'inference': 2048})
