import cv2
import numpy as np
import time
from flask import Flask, render_template, Response
from ultralytics import YOLO  


app = Flask(__name__)

#livestream
ESP32_STREAM_URL = "http://192.168.1.6:81/stream"

yolo_model = YOLO("yolov8n.pt") 

def detect_humans():
    cap = cv2.VideoCapture(ESP32_STREAM_URL)
    if not cap.isOpened():
        print("Error: Cannot open ESP32-CAM stream")
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
    cap.set(cv2.CAP_PROP_FPS, 15)

    retry_count = 0

    # motiondetection
    previous_centers_buffer = []
    buffer_size = 3
    T_lower = 12   
    T_upper = 18
    previous_statuses = []
    consistency_counters = []
    consistency_threshold = 2

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Frame retrieval failed! Trying again...")
            retry_count += 1
            time.sleep(0.5)
            if retry_count > 5:
                print("Error: Failed to retrieve frames, stopping stream.")
                break
            continue
        retry_count = 0

    
        results = yolo_model(frame)
        persons = []
        #first detection
        for result in results:
            if hasattr(result, 'boxes'):
                for box in result.boxes:

                    x1, y1, x2, y2 = list(map(int, box.xyxy[0].cpu().numpy()))
                    conf = float(box.conf[0].cpu().numpy())
                    cls = int(box.cls[0].cpu().numpy())
                    if cls == 0 and conf > 0.5:
                        persons.append((x1, y1, x2 - x1, y2 - y1))

        current_centers = []
        statuses = []

        for (x, y, w, h) in persons:
            cx, cy = x + w / 2, y + h / 2
            current_centers.append((cx, cy))
            new_status = "moving"
            if previous_centers_buffer:
                prev_all = [center for centers in previous_centers_buffer for center in centers]
                distances = [np.linalg.norm(np.array((cx, cy)) - np.array(prev)) for prev in prev_all]
                min_distance = min(distances) if distances else float('inf')
            else:
                min_distance = float('inf')
            
            if min_distance < T_lower:
                new_status = "still"
            elif min_distance > T_upper:
                new_status = "moving"
            else:
                if len(previous_statuses) > len(statuses):
                    new_status = previous_statuses[len(statuses)]
                else:
                    new_status = "moving"
            statuses.append(new_status)

        # Update-buffers 
        previous_centers_buffer.append(current_centers)
        if len(previous_centers_buffer) > buffer_size:
            previous_centers_buffer.pop(0)

        if previous_statuses and len(previous_statuses) == len(statuses):
            if len(consistency_counters) < len(statuses):
                consistency_counters = [0] * len(statuses)
            for i in range(len(statuses)):
                if statuses[i] != previous_statuses[i]:
                    consistency_counters[i] += 1
                    if consistency_counters[i] < consistency_threshold:
                        statuses[i] = previous_statuses[i]
                else:
                    consistency_counters[i] = 0
        else:
            consistency_counters = [0] * len(statuses)
        previous_statuses = statuses

        # boxes and labels 
        for idx, (x, y, w, h) in enumerate(persons):
            if statuses[idx] == "moving":
                box_color = (0, 0, 255)  # Red 
                label = "Moving"
            else:
                box_color = (0, 255, 0)  # Green 
                label = "Still"
            cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
            cv2.putText(frame, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        # frame to JPEG
        _, buffer_img = cv2.imencode('.jpg', frame)
        frame_bytes = buffer_img.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/motion_feed')
def motion_feed():
    return Response(detect_humans(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frame2')
def frame2():
    return render_template("frame2.html")

@app.route("/")
def home():
    return """
    <h1>Welcome to the Motion Detection App</h1>
    <p>Go to <a href="/frame2">Frame2</a> for the motion detection interface.</p>
    <p>Or view the <a href="/motion_feed">Motion Feed</a> directly.</p>
    """

if __name__ == '__main__':
    app.run(debug=True)
