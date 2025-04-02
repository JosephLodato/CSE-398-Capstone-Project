import cv2
import numpy as np
from flask import Flask, Response, render_template, send_file
from skimage.morphology import skeletonize
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

app = Flask(__name__)
cap = cv2.VideoCapture(1)  # Use 0 for built-in webcam, 1 for external

# Initialize a dummy frame to avoid None errors
last_frame = np.zeros((480, 640, 3), dtype=np.uint8)

@app.route('/')
def index():
    return render_template('index.html')

def generate_frames():
    global last_frame
    while True:
        success, frame = cap.read()
        if not success:
            continue
        last_frame = frame.copy()

        # Get the actual frame dimensions
        height, width = frame.shape[:2]

        # Draw resolution info on the frame
        text = f'Resolution: {width}x{height}'
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/snapshot')
def snapshot():
    global last_frame

    # Convert to grayscale and binary
    gray = cv2.cvtColor(last_frame, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    binary_bool = binary > 0
    skeleton = skeletonize(binary_bool).astype(np.uint8) * 255

    # Find contours
    contours, _ = cv2.findContours(skeleton, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Plot using object-oriented matplotlib
    fig = Figure(figsize=(8, 8))
    ax = fig.add_subplot(1, 1, 1)

    for contour in contours:
        coords = contour.reshape(-1, 2)
        if len(coords) > 1:
            xs, ys = zip(*coords)
            ax.plot(xs, ys, marker='.', linestyle='-', linewidth=0.5)

    ax.set_title("Skeleton Contours from Snapshot")
    ax.invert_yaxis()
    ax.axis('equal')
    ax.grid(True)

    buf = io.BytesIO()
    canvas = FigureCanvas(fig)
    canvas.print_png(buf)
    buf.seek(0)

    return send_file(buf, mimetype='image/png', download_name='snapshot.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
@app.route('/resolution')
def resolution():
    if cap.isOpened():
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return {"max_x": width - 1, "max_y": height - 1}
    return {"error": "Camera not available"}