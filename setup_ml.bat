@echo off
echo Setting up ML Model...

if not exist "ssd_mobilenet_v2_coco.tar.gz" (
    echo Downloading model...
    powershell -Command "Invoke-WebRequest -Uri 'http://download.tensorflow.org/models/object_detection/ssd_mobilenet_v2_coco_2018_03_29.tar.gz' -OutFile 'ssd_mobilenet_v2_coco.tar.gz'"
)

if not exist "models\ssd_mobilenet_v2_coco_2018_03_29.pbtxt" (
    echo Downloading config...
    powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/ssd_mobilenet_v2_coco_2018_03_29.pbtxt' -OutFile 'models\ssd_mobilenet_v2_coco_2018_03_29.pbtxt'"
)

echo Extracting model...
tar -xf ssd_mobilenet_v2_coco.tar.gz -C models

echo Done!
pause
