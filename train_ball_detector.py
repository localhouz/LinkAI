"""
Golf Ball Detection Model Training Script
Uses YOLOv8 to train a model for real-time ball detection
Exports to CoreML for on-device inference
"""

import os
import json
from pathlib import Path

# Check for ultralytics
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  ultralytics not installed. Run: pip install ultralytics")

# Check for coremltools
try:
    import coremltools as ct
    COREML_AVAILABLE = True
except ImportError:
    COREML_AVAILABLE = False
    print("⚠️  coremltools not installed. Run: pip install coremltools")


class GolfBallModelTrainer:
    """
    Trains a YOLOv8 model for golf ball detection and exports to CoreML.
    """
    
    def __init__(self, data_dir: str = "training_data", output_dir: str = "models"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Model configuration
        self.model_size = "n"  # nano for speed (n, s, m, l, x)
        self.image_size = 640
        self.epochs = 100
        self.batch_size = 16
        
    def create_dataset_yaml(self):
        """Creates YOLO dataset configuration file."""
        
        dataset_config = {
            "path": str(self.data_dir.absolute()),
            "train": "images/train",
            "val": "images/val",
            "test": "images/test",
            "names": {
                0: "golf_ball",
                1: "club_head"
            },
            "nc": 2  # number of classes
        }
        
        yaml_path = self.data_dir / "dataset.yaml"
        
        # Write YAML manually (to avoid pyyaml dependency)
        with open(yaml_path, 'w') as f:
            f.write(f"path: {dataset_config['path']}\n")
            f.write(f"train: {dataset_config['train']}\n")
            f.write(f"val: {dataset_config['val']}\n")
            f.write(f"test: {dataset_config['test']}\n")
            f.write(f"nc: {dataset_config['nc']}\n")
            f.write("names:\n")
            for idx, name in dataset_config['names'].items():
                f.write(f"  {idx}: {name}\n")
        
        print(f"✅ Created dataset config: {yaml_path}")
        return yaml_path
    
    def setup_directories(self):
        """Creates required directory structure for training data."""
        
        dirs = [
            self.data_dir / "images" / "train",
            self.data_dir / "images" / "val",
            self.data_dir / "images" / "test",
            self.data_dir / "labels" / "train",
            self.data_dir / "labels" / "val",
            self.data_dir / "labels" / "test",
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            
        print(f"✅ Created directory structure in {self.data_dir}")
        print("""
📁 training_data/
   ├── images/
   │   ├── train/     <- Place training images here
   │   ├── val/       <- Place validation images here
   │   └── test/      <- Place test images here
   └── labels/
       ├── train/     <- YOLO format labels (.txt)
       ├── val/
       └── test/

Label format (one .txt file per image):
<class_id> <x_center> <y_center> <width> <height>
Example: 0 0.5 0.5 0.1 0.1  (golf ball at center, 10% of image size)
""")
        
    def train(self):
        """Trains the YOLOv8 model."""
        
        if not YOLO_AVAILABLE:
            print("❌ Cannot train without ultralytics. Install it first.")
            return None
        
        yaml_path = self.create_dataset_yaml()
        
        # Load pretrained model
        model = YOLO(f"yolov8{self.model_size}.pt")
        
        print(f"""
🏌️ Starting Golf Ball Detection Training
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Model:      YOLOv8{self.model_size}
Image Size: {self.image_size}
Epochs:     {self.epochs}
Batch Size: {self.batch_size}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        
        # Train the model
        results = model.train(
            data=str(yaml_path),
            epochs=self.epochs,
            imgsz=self.image_size,
            batch=self.batch_size,
            project=str(self.output_dir),
            name="golf_ball_detector",
            exist_ok=True,
            device="0",  # Use GPU if available, else CPU
            patience=20,  # Early stopping
            save=True,
            plots=True,
        )
        
        # Get best model path
        best_model_path = self.output_dir / "golf_ball_detector" / "weights" / "best.pt"
        print(f"✅ Training complete! Best model: {best_model_path}")
        
        return best_model_path
    
    def export_to_coreml(self, model_path: str = None):
        """Exports trained model to CoreML format for iOS."""
        
        if not YOLO_AVAILABLE:
            print("❌ Cannot export without ultralytics.")
            return None
            
        if model_path is None:
            model_path = self.output_dir / "golf_ball_detector" / "weights" / "best.pt"
        
        if not Path(model_path).exists():
            print(f"❌ Model not found: {model_path}")
            return None
        
        model = YOLO(model_path)
        
        print("📱 Exporting to CoreML format...")
        
        # Export to CoreML
        coreml_path = model.export(
            format="coreml",
            imgsz=self.image_size,
            nms=True,  # Include NMS in model
        )
        
        print(f"✅ CoreML model exported: {coreml_path}")
        return coreml_path
    
    def export_to_tflite(self, model_path: str = None):
        """Exports trained model to TFLite format for Android."""
        
        if not YOLO_AVAILABLE:
            print("❌ Cannot export without ultralytics.")
            return None
            
        if model_path is None:
            model_path = self.output_dir / "golf_ball_detector" / "weights" / "best.pt"
        
        if not Path(model_path).exists():
            print(f"❌ Model not found: {model_path}")
            return None
        
        model = YOLO(model_path)
        
        print("🤖 Exporting to TFLite format...")
        
        # Export to TFLite
        tflite_path = model.export(
            format="tflite",
            imgsz=self.image_size,
        )
        
        print(f"✅ TFLite model exported: {tflite_path}")
        return tflite_path


def main():
    """Main entry point for training."""
    
    trainer = GolfBallModelTrainer(
        data_dir="training_data",
        output_dir="models"
    )
    
    # Setup directories for training data
    trainer.setup_directories()
    
    print("""
╔════════════════════════════════════════════════════════════════╗
║                 GOLF BALL DETECTION TRAINER                     ║
╠════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  1. Add training images to: training_data/images/train/         ║
║  2. Add label files to:     training_data/labels/train/         ║
║  3. Run this script again to start training                     ║
║                                                                  ║
║  Recommended: 1000+ images of golf balls in various conditions  ║
║  - Different lighting (sun, shade, overcast)                    ║
║  - Different backgrounds (grass, sand, sky)                     ║
║  - Ball in motion (blur) and stationary                         ║
║  - Various distances from camera                                ║
║                                                                  ║
╚════════════════════════════════════════════════════════════════╝
""")
    
    # Check if training data exists
    train_images = list((trainer.data_dir / "images" / "train").glob("*"))
    if len(train_images) > 0:
        print(f"Found {len(train_images)} training images. Starting training...")
        
        # Train the model
        model_path = trainer.train()
        
        if model_path:
            # Export to mobile formats
            trainer.export_to_coreml(model_path)
            trainer.export_to_tflite(model_path)
    else:
        print("⚠️  No training images found. Add images and run again.")


if __name__ == "__main__":
    main()
