from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException
from app.utils.storage import storage_manager, FileValidator
from app.utils.audit import AuditLogger


class FileService:
    
    @staticmethod
    async def upload_user_photo(
        file: UploadFile,
        file_type: str,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:

        try:
            file_content = await file.read()
            is_valid, error_message = FileValidator.validate_image(file_content, file.content_type)
            
            if not is_valid:
                return False, error_message, None
            
            success, url_or_error = storage_manager.upload_file(
                file_content, 
                file.filename, 
                file.content_type
            )
            
            if not success:
                return False, url_or_error, None
            
            AuditLogger.log_action(
                user_id=user_id,
                action="file_upload",
                resource="user_photo",
                details={
                    "file_type": file_type,
                    "original_filename": file.filename,
                    "content_type": file.content_type,
                    "size": len(file_content)
                },
                ip_address=ip_address
            )
            
            return True, "Archivo subido exitosamente", url_or_error
            
        except Exception as e:
            return False, f"Error subiendo archivo: {str(e)}", None
    
    @staticmethod
    async def upload_document_images(
        profile_photo: Optional[UploadFile] = None,
        document_front: Optional[UploadFile] = None,
        document_back: Optional[UploadFile] = None,
        user_id: str = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str, dict]:

        try:
            urls = {}
            
            if profile_photo:
                success, message, url = await FileService.upload_user_photo(
                    profile_photo, "profile", user_id, ip_address
                )
                if success:
                    urls["profile_photo_url"] = url
                else:
                    return False, f"Error subiendo foto de perfil: {message}", {}
            
            if document_front:
                success, message, url = await FileService.upload_user_photo(
                    document_front, "document_front", user_id, ip_address
                )
                if success:
                    urls["document_front_url"] = url
                else:
                    return False, f"Error subiendo documento frontal: {message}", {}
            
            if document_back:
                success, message, url = await FileService.upload_user_photo(
                    document_back, "document_back", user_id, ip_address
                )
                if success:
                    urls["document_back_url"] = url
                else:
                    return False, f"Error subiendo documento posterior: {message}", {}
            
            if not urls:
                return False, "No se subieron archivos", {}
            
            AuditLogger.log_action(
                user_id=user_id,
                action="document_upload",
                resource="user_documents",
                details={
                    "uploaded_files": list(urls.keys()),
                    "files_count": len(urls)
                },
                ip_address=ip_address
            )
            
            return True, "Archivos subidos exitosamente", urls
            
        except Exception as e:
            return False, f"Error subiendo documentos: {str(e)}", {}
    
    @staticmethod
    def validate_file_upload(file: UploadFile) -> Tuple[bool, str]:

        try:
            if not file.filename:
                return False, "Nombre de archivo requerido"
            
            if file.size and file.size > 5 * 1024 * 1024:  # 5MB
                return False, "Archivo demasiado grande (máximo 5MB)"
            
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            file_extension = file.filename.lower().split('.')[-1]
            
            if f'.{file_extension}' not in allowed_extensions:
                return False, f"Tipo de archivo no permitido. Extensiones permitidas: {', '.join(allowed_extensions)}"
            
            return True, "Archivo válido"
            
        except Exception as e:
            return False, f"Error validando archivo: {str(e)}"