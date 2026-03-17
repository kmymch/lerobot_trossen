#!/usr/bin/env python3
"""
GPU availability and compatibility check script.
Verifies CUDA support and RTX 5080 (sm_120) compatibility.
"""

import sys
import torch


def check_gpu():
    print("=" * 60)
    print("GPU AVAILABILITY AND COMPATIBILITY CHECK")
    print("=" * 60)
    
    # PyTorch version
    print(f"\n📦 PyTorch Version: {torch.__version__}")
    
    # CUDA availability
    print(f"🔧 CUDA Available: {torch.cuda.is_available()}")
    print(f"🔧 CUDA Version: {torch.version.cuda}")
    
    if not torch.cuda.is_available():
        print("\n❌ CUDA is not available. GPU support is disabled.")
        return False
    
    # Device count
    device_count = torch.cuda.device_count()
    print(f"📊 Device Count: {device_count}")
    
    # Device details
    for i in range(device_count):
        print(f"\n--- Device {i} ---")
        print(f"  Name: {torch.cuda.get_device_name(i)}")
        
        # Get compute capability
        compute_capability = torch.cuda.get_device_capability(i)
        sm_version = f"sm_{compute_capability[0]}{compute_capability[1]}"
        print(f"  Compute Capability: {compute_capability[0]}.{compute_capability[1]} ({sm_version})")
        
        # Memory info
        props = torch.cuda.get_device_properties(i)
        total_memory = props.total_memory / (1024 ** 3)
        print(f"  Total Memory: {total_memory:.2f} GB")
        
        # Check RTX 5080 (sm_120) support
        if compute_capability[0] == 1 and compute_capability[1] == 20:  # sm_120
            print(f"  ✅ RTX 5080 (sm_120) detected!")
            # Check if cu128 or higher is needed
            cuda_version = torch.version.cuda
            major, minor = map(int, cuda_version.split('.')[:2])
            cudnn_version = torch.backends.cudnn.version()
            print(f"     CUDA: {cuda_version}, cuDNN: {cudnn_version}")
            
            if major < 12 or (major == 12 and minor < 8):
                print(f"     ⚠️  WARNING: CUDA {cuda_version} may not fully support RTX 5080")
                print(f"     ➡️  Recommended: CUDA 12.8 or higher")
    
    # Test basic GPU operations
    print(f"\n--- GPU Operations Test ---")
    try:
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        print("✅ Basic tensor operations work on GPU")
        return True
    except Exception as e:
        print(f"❌ Error during GPU operations: {e}")
        return False


if __name__ == "__main__":
    success = check_gpu()
    sys.exit(0 if success else 1)
