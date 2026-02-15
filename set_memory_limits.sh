#!/bin/bash
# Memory Configuration Script for PyTorch/Python
# This script sets memory limits to allow using full 15GB RAM

echo "🔧 Configuring memory limits for Python/PyTorch..."

# 1. Remove ulimit restrictions (allow unlimited memory)
ulimit -v unlimited  # Virtual memory
ulimit -m unlimited  # Physical memory
ulimit -d unlimited  # Data segment
ulimit -s unlimited  # Stack size

# 2. PyTorch CUDA memory settings
export PYTORCH_CUDA_ALLOC_CONF="max_split_size_mb:512,expandable_segments:True"

# 3. PyTorch CPU memory settings
export OMP_NUM_THREADS=$(nproc)  # Use all CPU cores
export MKL_NUM_THREADS=$(nproc)

# 4. Python memory allocator (use system malloc for better large allocations)
export PYTHONMALLOC=malloc

# 5. Increase PyTorch tensor allocation size
export PYTORCH_MAX_TENSOR_SIZE=16000000000  # 16GB max tensor size

# 6. Allow oversubscription (use more than physical RAM if needed)
export MALLOC_ARENA_MAX=2  # Reduce memory fragmentation

# 7. For CUDA: Allow PyTorch to use all available GPU memory
export PYTORCH_NO_CUDA_MEMORY_CACHING=0  # Enable caching for efficiency

echo "✅ Memory limits configured:"
echo "   Virtual memory: $(ulimit -v)"
echo "   Physical memory: $(ulimit -m)"
echo "   CPU threads: $OMP_NUM_THREADS"
echo "   PyTorch config: $PYTORCH_CUDA_ALLOC_CONF"
echo ""
echo "Now run your uncensor command in this same terminal:"
echo "  python uncensor_standalone.py --input image.jpg --no-downscale --device cuda"
