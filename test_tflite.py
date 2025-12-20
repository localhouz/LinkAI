"""
Test if TensorFlow Lite can load the model without hanging
"""
import sys
print("Importing TensorFlow...")
sys.stdout.flush()

import tensorflow as tf
print(f"TensorFlow version: {tf.__version__}")
sys.stdout.flush()

print("Loading TFLite model...")
sys.stdout.flush()

try:
    interpreter = tf.lite.Interpreter(model_path="models/detect.tflite")
    print("Allocating tensors...")
    sys.stdout.flush()
    
    interpreter.allocate_tensors()
    print("✓ TFLite model loaded successfully!")
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    print(f"Input shape: {input_details[0]['shape']}")
    print(f"Input dtype: {input_details[0]['dtype']}")
    print(f"Number of outputs: {len(output_details)}")
    
except Exception as e:
    print(f"✗ Error loading TFLite model: {e}")
    import traceback
    traceback.print_exc()
