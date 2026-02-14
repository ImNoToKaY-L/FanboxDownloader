#!/usr/bin/env python3
"""
Standalone Image Uncensoring Tool
Removes mosaic/pixelation censorship from images using AI inpainting.
"""

import sys
import argparse
import logging
from pathlib import Path
from fanbox_scraper.uncensor import ImageUncensor


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('uncensor.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Main entry point for standalone uncensor tool."""
    parser = argparse.ArgumentParser(
        description='Uncensor images by removing mosaic/pixelation censorship',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Uncensor single image with auto-detection
  python uncensor_standalone.py --input image.jpg --output uncensored.jpg

  # Uncensor with manual mask
  python uncensor_standalone.py --input image.jpg --mask mask.png --output uncensored.jpg

  # Batch process directory
  python uncensor_standalone.py --input-dir downloads/ --output-dir uncensored/

  # Use GPU with high sensitivity for small mosaics
  python uncensor_standalone.py --input-dir downloads/ --device cuda --sensitivity 0.8

  # Very high sensitivity for tiny/subtle censorship
  python uncensor_standalone.py --input image.jpg --sensitivity 0.9 --device cuda

  # Disable auto-detection (requires manual masks)
  python uncensor_standalone.py --input-dir images/ --mask-dir masks/ --no-auto-detect

Notes:
  - Requires PyTorch and uncensor dependencies: pip install -r requirements-uncensor.txt
  - Auto-detection works best on clear mosaic patterns
  - Use higher sensitivity (0.7-0.9) for small/subtle mosaics
  - GPU highly recommended for batch processing
  - First run will download model (~200MB)
        """
    )

    # Input/Output
    parser.add_argument(
        '--input',
        help='Input image path (for single image)'
    )
    parser.add_argument(
        '--output',
        help='Output image path (for single image)'
    )
    parser.add_argument(
        '--input-dir',
        help='Input directory (for batch processing)'
    )
    parser.add_argument(
        '--output-dir',
        default='uncensored',
        help='Output directory (default: uncensored)'
    )

    # Mask options
    parser.add_argument(
        '--mask',
        help='Mask image path (white=uncensor, black=keep)'
    )
    parser.add_argument(
        '--mask-dir',
        help='Directory containing mask images (for batch processing)'
    )
    parser.add_argument(
        '--no-auto-detect',
        action='store_true',
        help='Disable automatic censorship detection'
    )
    parser.add_argument(
        '--detection-threshold',
        type=float,
        default=0.7,
        help='Detection confidence threshold 0-1 (default: 0.7)'
    )
    parser.add_argument(
        '--sensitivity',
        type=float,
        default=0.5,
        help='Detection sensitivity 0.0-1.0 (default: 0.5). '
             'Use 0.7-0.9 for small/subtle mosaics. '
             'Higher values may increase false positives.'
    )
    parser.add_argument(
        '--max-resolution',
        type=int,
        default=2048,
        help='Max image dimension for processing (default: 2048). '
             'Use 1024 for low memory systems, 4096 for high-end GPUs'
    )

    # Model options
    parser.add_argument(
        '--device',
        choices=['cpu', 'cuda', 'mps'],
        default='cpu',
        help='Device to use (default: cpu). Use cuda for NVIDIA GPU, mps for Apple Silicon'
    )
    parser.add_argument(
        '--model',
        choices=['lama'],
        default='lama',
        help='Model to use (default: lama)'
    )
    parser.add_argument(
        '--cache-dir',
        default='models',
        help='Model cache directory (default: models)'
    )

    # Additional options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Show processing statistics'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Validate input
    if not args.input and not args.input_dir:
        parser.error("Either --input or --input-dir must be specified")

    if args.input and args.input_dir:
        parser.error("Cannot specify both --input and --input-dir")

    # Check dependencies
    try:
        import torch
        logger.info(f"PyTorch version: {torch.__version__}")
        logger.info(f"CUDA available: {torch.cuda.is_available()}")
    except ImportError:
        logger.error("PyTorch not installed. Install with: pip install -r requirements-uncensor.txt")
        return 1

    print("=" * 70)
    print("Image Uncensoring Tool - Mosaic/Pixelation Removal")
    print("=" * 70)

    try:
        # Initialize uncensor
        uncensor = ImageUncensor(
            device=args.device,
            model_type=args.model,
            auto_detect=not args.no_auto_detect,
            output_dir=args.output_dir,
            cache_dir=args.cache_dir,
            sensitivity=args.sensitivity,
            max_resolution=args.max_resolution
        )

        logger.info(f"Sensitivity level: {args.sensitivity:.2f} "
                   f"({'low' if args.sensitivity < 0.4 else 'medium' if args.sensitivity < 0.7 else 'high' if args.sensitivity < 0.9 else 'very high'})")
        logger.info(f"Max resolution: {args.max_resolution}px (images will be downscaled if larger)")

        # Process single image
        if args.input:
            logger.info(f"Processing single image: {args.input}")

            if not Path(args.input).exists():
                logger.error(f"Input file not found: {args.input}")
                return 1

            output_path = uncensor.uncensor_image(
                image_path=args.input,
                mask_path=args.mask,
                output_path=args.output
            )

            if output_path:
                print(f"\n✓ Success! Uncensored image saved to: {output_path}")
                return 0
            else:
                print("\n✗ Failed to uncensor image")
                return 1

        # Process directory
        elif args.input_dir:
            logger.info(f"Processing directory: {args.input_dir}")

            input_dir = Path(args.input_dir)
            if not input_dir.exists():
                logger.error(f"Input directory not found: {args.input_dir}")
                return 1

            # Find all images
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
            image_paths = [
                str(p) for p in input_dir.iterdir()
                if p.suffix.lower() in image_extensions
            ]

            if not image_paths:
                logger.error(f"No images found in {args.input_dir}")
                return 1

            print(f"\nFound {len(image_paths)} images to process")
            print("-" * 70)

            # Batch process
            results = uncensor.batch_uncensor(
                image_paths=image_paths,
                mask_dir=args.mask_dir,
                show_progress=True
            )

            print("\n" + "=" * 70)
            print("Batch Processing Complete!")
            print("=" * 70)
            print(f"Successfully uncensored: {len(results['success'])}")
            print(f"Failed: {len(results['failed'])}")

            if results['failed']:
                print("\nFailed images:")
                for path in results['failed']:
                    print(f"  - {path}")

            print(f"\nOutput directory: {args.output_dir}")

            if args.stats:
                print("\n" + "-" * 70)
                print("Statistics:")
                print("-" * 70)
                stats = uncensor.get_stats()
                for key, value in stats.items():
                    print(f"  {key}: {value}")

            return 0 if results['failed'] == [] else 1

    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user.")
        return 130

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # Cleanup
        if 'uncensor' in locals():
            uncensor.cleanup()


if __name__ == '__main__':
    sys.exit(main())
