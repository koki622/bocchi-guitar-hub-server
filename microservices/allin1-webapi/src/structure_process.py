import sys
from datetime import datetime
from pathlib import Path
import demucs
import torch
from allin1.helpers import run_inference
from allin1.models.loaders import load_pretrained_model
from utility import adjust_segments_to_beat, analysis_result_to_json, generate_click_sound

def analyze_structure(file_path, spec_path, device):
    file_path = Path(file_path)
    spec_path = Path(spec_path)
    with torch.no_grad():
        result = run_inference(
            path=file_path,
            spec_path=spec_path,
            model=load_pretrained_model(device=device),
            device=device,
            include_activations=False,
            include_embeddings=False
        )
    print('音楽構造の解析が完了')
    save_dir = Path(file_path.parent / 'structure')
    save_dir.mkdir()

    # 曲のセクションのタイミングをビートに補正
    result.segments = adjust_segments_to_beat(result.beats, result.segments)

    # 結果をjsonとして保存
    analysis_result_to_json(result, save_dir)

    y = demucs.separate.load_track(file_path, 2, 44100).numpy()
    length = y.shape[-1]
    # ビートの結果からクリック音を生成
    generate_click_sound(result, length, save_dir)
    
    end_time = datetime.now()
    return {"end": end_time}

if __name__ == "__main__":
    file_path = sys.argv[1] 
    spec_path = sys.argv[2] 
    device = sys.argv[3]  

    result = analyze_structure(file_path, spec_path, device)
