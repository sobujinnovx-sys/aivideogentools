try:
    import torch
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
    else:
        print("No CUDA GPU detected")
except ImportError:
    print("PyTorch not installed")

try:
    import diffusers
    print(f"Diffusers: {diffusers.__version__}")
except ImportError:
    print("Diffusers not installed")

try:
    import transformers
    print(f"Transformers: {transformers.__version__}")
except ImportError:
    print("Transformers not installed")
