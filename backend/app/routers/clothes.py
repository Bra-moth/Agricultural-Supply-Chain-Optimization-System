from fastapi import APIRouter, UploadFile
from ..services.ai import tag_clothing
from ..models import ClothingItem

router = APIRouter(prefix="/clothes")

@router.post("/upload")
async def upload_clothing(file: UploadFile, user_id: str):
    # Save image to S3/Cloudinary
    attributes = tag_clothing(file.file)
    new_item = ClothingItem(user_id=user_id, image_url="s3_url", attributes=attributes)
    # Save to DB (pseudo-code)
    return {"item_id": new_item.id}