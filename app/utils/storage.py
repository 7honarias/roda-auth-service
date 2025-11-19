
import uuid
from typing import Tuple
from pathlib import Path
from google.cloud import storage as gcs
from app.config.settings import settings


class CloudStorageManager:
    
    def __init__(self):
        self.provider = settings.CLOUD_PROVIDER.lower()
        self.gcs_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        try:
            
            self.gcs_client = gcs.Client()
        except Exception as e:
            print(f"Error inicializando cliente de almacenamiento: {e}")
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str) -> Tuple[bool, str]:

        try:
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            return self._upload_to_gcs(file_content, unique_filename, content_type)
            
        except Exception as e:
            return False, f"Error subiendo archivo: {str(e)}"
    
    
    def _upload_to_gcs(self, file_content: bytes, filename: str, content_type: str) -> Tuple[bool, str]:
        try:
            if not self.gcs_client:
                return False, "Cliente GCS no configurado"
            
            bucket = self.gcs_client.bucket(settings.GCP_BUCKET_NAME)
            blob = bucket.blob(filename)
            
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            blob.make_public()
            
            return True, blob.public_url
            
        except Exception as e:
            return False, f"Error subiendo a GCS: {str(e)}"


class FileValidator:
    
    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg", 
        "image/png": ".png",
        "image/webp": ".webp"
    }
    
    MAX_FILE_SIZE = 5 * 1024 * 1024
    
    @classmethod
    def validate_image(cls, file_content: bytes, content_type: str) -> Tuple[bool, str]:

        if content_type not in cls.ALLOWED_IMAGE_TYPES:
            return False, f"Tipo de archivo no permitido. Tipos permitidos: {list(cls.ALLOWED_IMAGE_TYPES.keys())}"
        
        if len(file_content) > cls.MAX_FILE_SIZE:
            return False, f"Archivo demasiado grande. Tamaño máximo: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
        
        if len(file_content) < 100:  
            return False, "Archivo demasiado pequeño para ser una imagen válida"
        
        return True, "Archivo válido"

storage_manager = CloudStorageManager()