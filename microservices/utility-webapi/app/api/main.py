from fastapi import APIRouter

from app.api.routes import demucs

api_router = APIRouter()
#api_router.include_router(allin1.router, prefix='/allin1', tags=['allin1'])
#api_router.include_router(crema.router, prefix='/crema', tags=['crema'])
api_router.include_router(demucs.router, prefix='/demucs', tags=['demucs'])
#api_router.include_router(whisper.router, prefix='/whisper', tags=['whisper'])