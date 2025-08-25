import cv2
import threading

class Camera:
    def __init__(self):
        # 0 genellikle bilgisayarın dahili kamerasını temsil eder.
        # Eğer başka bir kamera kullanmak isterseniz bu sayıyı değiştirebilirsiniz (1, 2, vb.).
        self.video = cv2.VideoCapture(0)
        if not self.video.isOpened():
            raise RuntimeError("Kamera başlatılamadı. Başka bir program tarafından kullanılıyor olabilir mi?")
        
        # Kameradan okunan son kareyi ve bu kare için bir kilit tutar
        self.frame = None
        self.lock = threading.Lock()
        
        # Arka planda sürekli olarak kameradan kare okuyacak bir thread başlat
        self.thread = threading.Thread(target=self._update, args=())
        self.thread.daemon = True
        self.thread.start()

    def _update(self):
        # Bu fonksiyon, thread içinde çalışarak sürekli olarak kameradan en güncel kareyi okur.
        while True:
            ret, frame = self.video.read()
            if ret:
                with self.lock:
                    self.frame = frame

    def get_frame(self):
        # En son okunan kareyi JPEG formatına dönüştürerek döndürür.
        # Bu, web üzerinden akış için kullanılır.
        with self.lock:
            if self.frame is None:
                return None
            
            # Kareyi JPEG formatına encode et
            ret, jpeg = cv2.imencode('.jpg', self.frame)
            if not ret:
                return None
            return jpeg.tobytes()

    def get_snapshot_frame(self):
        # Anlık görüntü almak için o anki kareyi döndürür.
        # Bu fonksiyon, görüntüyü diske kaydetmek için ham (encode edilmemiş) kareyi verir.
        with self.lock:
            if self.frame is None:
                return None, None
            return True, self.frame.copy()

    def __del__(self):
        # Nesne silindiğinde kamerayı serbest bırakır.
        self.video.release()
