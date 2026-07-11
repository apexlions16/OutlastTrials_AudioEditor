from .common import *

class EasterEggLoader(QObject):
    config_loaded = pyqtSignal(dict)    
    image_loaded = pyqtSignal(object)    
    loading_failed = pyqtSignal(str)    
    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.parent_app = parent_app
    def load_config(self):
        import threading
        
        def download_config():
            try:
                import requests
                import json
 
                config_url = "https://raw.githubusercontent.com/Bezna/OutlastTrials_AudioEditor/refs/heads/main/data/nothing.json"
                
                headers = {
                    'User-Agent': 'OutlastTrials_AudioEditor/1.0',
                    'Accept': 'application/json',
                }
                
                response = requests.get(config_url, timeout=10, headers=headers)
                response.raise_for_status()
                
                config = response.json()
                print(f"Config loaded successfully: {config}")
                
                self.config_loaded.emit(config)
                
            except Exception as e:
                print(f"Failed to load config: {e}")
                
                default_config = {
                    "easter_egg_image": "https://i.imgur.com/VeWWVDN.png",
                    "message": self.parent_app.tr('easter_egg_message'),
                    "version": "fallback"
                }
                self.config_loaded.emit(default_config)
        
        thread = threading.Thread(target=download_config)
        thread.daemon = True
        thread.start()
    
    def load_image(self, image_url):
        import threading
        
        def download_image():
            try:
                import requests
                from PyQt5.QtGui import QPixmap
                import time
                
                if not image_url:
                    raise Exception("No image URL provided")
                
                print(f"Loading image from: {image_url}")
                
                time.sleep(0.5)  
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/*',
                }
                
                response = requests.get(image_url, timeout=15, headers=headers)
                response.raise_for_status()
                
                print(f"Image downloaded, size: {len(response.content)} bytes")
                
                pixmap = QPixmap()
                success = pixmap.loadFromData(response.content)
                
                if success and not pixmap.isNull():
                    print("Image loaded successfully")
                    self.image_loaded.emit(pixmap)
                else:
                    raise Exception("Failed to create QPixmap")
                    
            except Exception as e:
                print(f"Failed to load image: {e}")
                self.loading_failed.emit(str(e))
        
        thread = threading.Thread(target=download_image)
        thread.daemon = True
        thread.start()
