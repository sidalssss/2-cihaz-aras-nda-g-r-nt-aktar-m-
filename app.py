import os
import time
from flask import Flask, render_template, Response, jsonify
from camera import Camera
import cv2

app = Flask(__name__)

# Kamera nesnesini global olarak oluşturuyoruz.
# Bu sayede uygulama çalıştığı sürece tek bir kamera nesnesi kullanılır.
try:
    camera = Camera()
except RuntimeError as e:
    print(f"Hata: {e}")
    camera = None

# Anlık görüntülerin kaydedileceği klasör
SNAPSHOTS_FOLDER = 'snapshots'
if not os.path.exists(SNAPSHOTS_FOLDER):
    os.makedirs(SNAPSHOTS_FOLDER)

def generate_frames():
    """
    Kameradan sürekli olarak kareler alır, JPEG formatına dönüştürür
    ve bir HTTP multipart response olarak yayınlar.
    """
    if not camera:
        print("Kamera mevcut değil, video akışı başlatılamıyor.")
        return

    while True:
        frame = camera.get_frame()
        if frame is None:
            # Kameradan geçerli bir kare alınamazsa döngüyü kır.
            # Bu durum kamera bağlantısı kesildiğinde olabilir.
            break
        
        # HTTP multipart formatında her bir kareyi yayınla
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Ana sayfayı render eder."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video akışını sağlayan URL yolu."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_snapshot')
def capture_snapshot():
    """
    Anlık bir kamera görüntüsü yakalar ve sunucudaki 'snapshots' klasörüne kaydeder.
    """
    if not camera:
        return jsonify({'success': False, 'message': 'Kamera bulunamadı.'})

    ret, frame = camera.get_snapshot_frame()
    if not ret:
        return jsonify({'success': False, 'message': 'Kare yakalanamadı.'})

    # Dosya adını zaman damgası ile oluştur
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"snapshot_{timestamp}.jpg"
    filepath = os.path.join(SNAPSHOTS_FOLDER, filename)

    # Görüntüyü dosyaya yaz
    try:
        cv2.imwrite(filepath, frame)
        print(f"Görüntü kaydedildi: {filepath}")
        return jsonify({'success': True, 'path': filepath})
    except Exception as e:
        print(f"Görüntü kaydedilirken hata oluştu: {e}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # '0.0.0.0' adresi, sunucunun aynı ağdaki diğer cihazlar tarafından
    # erişilebilir olmasını sağlar.
    app.run(host='0.0.0.0', port=5001, debug=True, threaded=True)
