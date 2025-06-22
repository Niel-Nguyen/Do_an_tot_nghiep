from fastapi import APIRouter, UploadFile, File
import shutil
from config.settings import settings

router = APIRouter()

@router.post("/upload-data")
def upload_data_file(file: UploadFile = File(...)):
    try:
        with open(settings.DATA_FILE_PATH, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "ok", "message": "Đã tải file dữ liệu"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
