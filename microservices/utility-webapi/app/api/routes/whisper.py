from enum import Enum
import json
import os
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sse_starlette import EventSourceResponse
from app.api.deps import get_audiofile, get_heavy_job
from app.core.heavy_job import ApiJob, HeavyJob
from app.core.config import settings
from app.models import Audiofile

router = APIRouter()

class LanguageCode(str, Enum):
    af = "af"
    am = "am"
    ar = "ar"
    as_code = "as"
    az = "az"
    ba = "ba"
    be = "be"
    bg = "bg"
    bn = "bn"
    bo = "bo"
    br = "br"
    bs = "bs"
    ca = "ca"
    cs = "cs"
    cy = "cy"
    da = "da"
    de = "de"
    el = "el"
    en = "en"
    es = "es"
    et = "et"
    eu = "eu"
    fa = "fa"
    fi = "fi"
    fo = "fo"
    fr = "fr"
    gl = "gl"
    gu = "gu"
    ha = "ha"
    haw = "haw"
    he = "he"
    hi = "hi"
    hr = "hr"
    ht = "ht"
    hu = "hu"
    hy = "hy"
    id = "id"
    is_code = "is"
    it = "it"
    ja = "ja"
    jw = "jw"
    ka = "ka"
    kk = "kk"
    km = "km"
    kn = "kn"
    ko = "ko"
    la = "la"
    lb = "lb"
    ln = "ln"
    lo = "lo"
    lt = "lt"
    lv = "lv"
    mg = "mg"
    mi = "mi"
    mk = "mk"
    ml = "ml"
    mn = "mn"
    mr = "mr"
    ms = "ms"
    mt = "mt"
    my = "my"
    ne = "ne"
    nl = "nl"
    nn = "nn"
    no = "no"
    oc = "oc"
    pa = "pa"
    pl = "pl"
    ps = "ps"
    pt = "pt"
    ro = "ro"
    ru = "ru"
    sa = "sa"
    sd = "sd"
    si = "si"
    sk = "sk"
    sl = "sl"
    sn = "sn"
    so = "so"
    sq = "sq"
    sr = "sr"
    su = "su"
    sv = "sv"
    sw = "sw"
    ta = "ta"
    te = "te"
    tg = "tg"
    th = "th"
    tk = "tk"
    tl = "tl"
    tr = "tr"
    tt = "tt"
    uk = "uk"
    ur = "ur"
    uz = "uz"
    vi = "vi"
    yi = "yi"
    yo = "yo"
    zh = "zh"
    yue = "yue"
    
@router.post("/lyric/{audiofile_id}")
def analyze_lyric(
    request: Request, 
    language_code: LanguageCode = Query(LanguageCode.ja, alias='language-code'),
    audiofile: Audiofile = Depends(get_audiofile), 
    job_router: HeavyJob = Depends(get_heavy_job)) -> EventSourceResponse:
    if os.path.exists(audiofile.audiofile_directory / 'lyric.txt'):
        raise HTTPException(
            status_code=400,
            detail='既に歌詞解析がされています。'
        )
    if not os.path.exists(audiofile.audiofile_directory / 'separated'):
        raise HTTPException(
            status_code=400,
            detail='音声の分離結果が見つかりませんでした。解析には音声の分離結果が必要です。'
        )
    
    file_path = str(audiofile.audiofile_directory / 'separated' / 'vocals.wav')
    request_body = {'file_path': file_path, 'language_code': language_code}
    api_job = ApiJob(
        job_name=settings.WHISPER_JOB_NAME,
        dst_api_url=f'http://{settings.WHISPER_HOST}:{8000}',
        queue_name=settings.WHISPER_JOB_QUEUE,
        request_path='/',
        job_timeout=settings.WHISPER_JOB_TIMEOUT,
        request_body=request_body,
        request_read_timeout=settings.WHISPER_JOB_TIMEOUT,
    )

    job = job_router.submit_jobs([api_job])[0]
    return EventSourceResponse(
        job_router.stream_job_status(request=request, job=job)
    )

@router.get('/lyric/{audiofile_id}')
def response_lyric(audiofile: Audiofile = Depends(get_audiofile)):
    with open(audiofile.audiofile_directory / 'lyric.txt') as f:
        return json.load(f)