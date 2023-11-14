# pm2 start src/video_capture.py --name thermal_capture
# pm2 start src/video_capture.py --name color_capture
# pm2 start src/detector.py --name thermal_detector -- 1
# pm2 start src/detector.py --name color_detector -- 2
pm2 start src/pyside_app.py