from fastapi import APIRouter

from app.api.routes import demucs, audiofile, consumer, util, whisper, crema, allin1, async_job

api_router = APIRouter()
api_router.include_router(allin1.router, prefix='/allin1', tags=['allin1'])
api_router.include_router(crema.router, prefix='/crema', tags=['crema'])
api_router.include_router(demucs.router, prefix='/demucs', tags=['demucs'])
api_router.include_router(whisper.router, prefix='/whisper', tags=['whisper'])
api_router.include_router(async_job.router, prefix='/async-job', tags=['async-job'])
api_router.include_router(audiofile.router, prefix='/audiofile', tags=['audiofile'])
api_router.include_router(util.router, prefix='/util', tags=['util'])
api_router.include_router(consumer.router, prefix='/consumer', tags=['consumer'])