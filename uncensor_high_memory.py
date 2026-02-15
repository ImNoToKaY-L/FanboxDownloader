#!/usr/bin/env python3
"""
High-Memory Mode Uncensor Tool
Configures Python/PyTorch for maximum memory usage before running uncensor.
Use this when you have 16GB+ RAM and want to process large images at full resolution.
"""

import os
import sys
import subprocess

def configure_high_memory_mode():
    """Configure environment for maximum memory usage."""
    print("🚀 Configuring HIGH MEMORY mode for PyTorch...")

    # 1. PyTorch CUDA memory allocation
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512,expandable_segments:True'

    # 2. CPU threading (use all cores)
    import multiprocessing
    num_cores = multiprocessing.cpu_count()
    os.environ['OMP_NUM_THREADS'] = str(num_cores)
    os.environ['MKL_NUM_THREADS'] = str(num_cores)

    # 3. Python memory allocator
    os.environ['PYTHONMALLOC'] = 'malloc'

    # 4. PyTorch tensor size limits
    os.environ['PYTORCH_MAX_TENSOR_SIZE'] = '16000000000'  # 16GB

    # 5. Reduce memory fragmentation
    os.environ['MALLOC_ARENA_MAX'] = '2'

    # 6. PyTorch memory caching
    os.environ['PYTORCH_NO_CUDA_MEMORY_CACHING'] = '0'

    # 7. Set resource limits (Linux only)
    try:
        import resource
        # Set to unlimited (RLIM_INFINITY)
        resource.setrlimit(resource.RLIMIT_AS, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_DATA, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
        print(f"✅ Resource limits set to unlimited")
    except Exception as e:
        print(f"⚠️  Could not set resource limits: {e}")

    print(f"✅ High-memory mode configured:")
    print(f"   CPU Threads: {num_cores}")
    print(f"   PyTorch CUDA: {os.environ['PYTORCH_CUDA_ALLOC_CONF']}")
    print(f"   Max Tensor Size: 16GB")
    print(f"   Memory Allocator: system malloc")
    print()

    # Import torch to verify configuration
    try:
        import torch
        print(f"📊 PyTorch Memory Status:")
        print(f"   CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
            print(f"   GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print()
    except ImportError:
        pass

def main():
    """Run uncensor_standalone.py with high-memory configuration."""
    # Configure memory first
    configure_high_memory_mode()

    # Import and run the original script
    print("🎨 Starting uncensor with high-memory mode...\n")

    # Change to uncensor_standalone directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    uncensor_script = os.path.join(script_dir, 'uncensor_standalone.py')

    if not os.path.exists(uncensor_script):
        print(f"❌ Error: uncensor_standalone.py not found at {uncensor_script}")
        sys.exit(1)

    # Run uncensor_standalone.py with all passed arguments
    # Use subprocess to ensure environment variables are inherited
    cmd = [sys.executable, uncensor_script] + sys.argv[1:]

    try:
        result = subprocess.run(cmd, env=os.environ.copy())
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running uncensor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
