from fastapi import APIRouter

router = APIRouter()

@router.get('/server-status', description='okを返すだけ。')
def responseOk():
    return 'ok'