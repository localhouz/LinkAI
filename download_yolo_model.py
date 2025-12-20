"""
Download YOLOv8-nano ONNX Model for Ball Detection

YOLOv8 is pre-trained on COCO dataset which includes "sports ball" class.
This script downloads the ONNX version for fast inference.
"""

import os
import urllib.request
import sys


def download_yolov8_onnx():
    """Download YOLOv8-nano ONNX model."""
    
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, "yolov8n.onnx")
    
    if os.path.exists(model_path):
        print(f"✅ Model already exists: {model_path}")
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"   Size: {file_size:.1f} MB")
        return model_path
    
    print("📥 Downloading YOLOv8-nano ONNX model...")
    print("   This may take a few minutes (~6 MB)")
    
    # Official YOLOv8 ONNX model from Ultralytics
    url = "https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.onnx"
    
    try:
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded / total_size * 100, 100)
            bar_length = 40
            filled = int(bar_length * percent / 100)
            bar = '█' * filled + '░' * (bar_length - filled)
            sys.stdout.write(f'\r   [{bar}] {percent:.1f}%')
            sys.stdout.flush()
        
        urllib.request.urlretrieve(url, model_path, progress_hook)
        print("\n✅ Download complete!")
        
        file_size = os.path.getsize(model_path) / (1024 * 1024)
        print(f"   Saved to: {model_path}")
        print(f"   Size: {file_size:.1f} MB")
        
        return model_path
        
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nManual download instructions:")
        print("1. Go to: https://github.com/ultralytics/assets/releases")
        print("2. Download yolov8n.onnx")
        print(f"3. Save to: {model_path}")
        return None


def export_custom_yolo():
    """
    Alternative: Export custom YOLOv8 model using ultralytics package.
    Run this if you want to train on custom golf ball data.
    """
    print("\n📦 To export a custom YOLOv8 model:")
    print("=" * 60)
    print("1. Install ultralytics:")
    print("   pip install ultralytics")
    print("\n2. Export pre-trained model to ONNX:")
    print("   from ultralytics import YOLO")
    print("   model = YOLO('yolov8n.pt')")
    print("   model.export(format='onnx')")
    print("\n3. Or train on custom golf ball dataset:")
    print("   model.train(data='golf_balls.yaml', epochs=100)")
    print("   model.export(format='onnx')")
    print("=" * 60)


if __name__ == "__main__":
    print("YOLOv8 ONNX Model Downloader")
    print("=" * 60)
    
    model_path = download_yolov8_onnx()
    
    if model_path:
        print("\n✅ Ready to use!")
        print("\nUsage in code:")
        print("  from hybrid_detector import HybridBallDetector")
        print(f"  detector = HybridBallDetector('{model_path}')")
    else:
        print("\n⚠️  Fallback to Hough-only mode")
        print("  detector = HybridBallDetector()  # No YOLO")
    
    print("\n" + "=" * 60)
    export_custom_yolo()
