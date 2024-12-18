import json
import os
from pathlib import Path
from typing import List, TypeVar, Union
from fastapi import HTTPException
import numpy as np
import pandas
from pydantic import BaseModel, field_validator

class ConsumerHeaders(BaseModel):
    consumer_id: str

class Consumer(ConsumerHeaders):
    consumer_directory: Path

    @field_validator('consumer_directory', mode='before')
    def check_consumer_directory_exists(cls, v: Path) -> Path:
        if os.path.exists(v):
            return v
        else:
            raise HTTPException(
                status_code=400,
                detail='コンシューマーディレクトリが存在しません。'
            )

class ConsumerCreate(ConsumerHeaders):
    pass
        
class AudiofileCreateResponse(BaseModel):
    audiofile_id: str

class Audiofile(Consumer):
    audiofile_id: str
    audiofile_directory: Path
    audiofile_path: Path

    @field_validator('audiofile_directory', mode='before')
    def check_audiofile_directory_exists(cls, v:Path) -> Path:
        if os.path.exists(v):
            return v
        else:
            raise HTTPException(
                status_code=400,
                detail='音声ファイルディレクトリが存在しません。'
            )

class CsvConvertibleBase(BaseModel):
    def to_csv(self, save_path: Path, target_property_names: List[str] = None):
        """自身のインスタンスが持つプロパティをCSVに変換して保存します。

        Args:
            save_path (Path): CSVファイルの保存先。
            target_property_names (List[str], optional): 対象のプロパティ名。Noneの場合はすべてのプロパティが対象になります。

        Raises:
            ValueError: インスタンスに存在しないプロパティが引数に渡される。
        """
        # target_property_namesがNoneの場合、インスタンスの全プロパティを使用
        if target_property_names is None:
            target_property_names = list(self.__annotations__.keys())

        data = {}
        # プロパティの値を取得し、辞書に格納
        for prop in target_property_names:
            if prop not in self.__annotations__:
                raise ValueError(f'Property {prop} does not exist in model.')
            
            value = getattr(self, prop)
            
            if isinstance(value, list) and value and isinstance(value[0], BaseModel):
                # List[BaseModel]の場合、各モデルを辞書に変換してDataFrameにする
                data[prop] = pandas.DataFrame([item.dict() for item in value])
            else:
                # それ以外の単純なリストや値を直接格納
                data[prop] = pandas.DataFrame({prop: value if isinstance(value, list) else [value]})

        # 各データフレームを横に連結
        df = pandas.concat(data.values(), axis=1)

        df.to_csv(save_path, index=False)

class JsonLoadableBase(CsvConvertibleBase):
    @classmethod
    def load_from_json_file(cls, json_path: Path):
        """対象のJSONファイルを読み取り、呼び出し元のPydantic モデルに変換します。

        Args:
            json_path (Path): 変換したいJSONファイルのパス。

        Returns:
            _type_: 呼び出し元のPydanticモデル。
        """
        with open(json_path) as f:
            data = json.load(f)
        model = cls.model_validate(data)
    
        return model
    
    def save_as_json_file(self, save_path: Path):
        json_data = self.model_dump_json()
        with open(save_path, 'w') as f:
            f.write(json_data)
    
class Chord(BaseModel):
    time: float
    duration: float
    value: str

class AdjustedChord(Chord):
    was_adjusted: bool

class ChordList(JsonLoadableBase):
    chords: List[Chord]

class AdjustedChordList(JsonLoadableBase):
    chords: List[AdjustedChord]

class Segment(BaseModel):
    start: float
    end: float
    label: str

TStructure = TypeVar('T', bound='Structure')

class Structure(JsonLoadableBase):
    bpm: int
    beats: List[float]
    downbeats: List[float]
    beat_positions: List[Union[int, float]]
    segments: List[Segment]

    def calculate_bpm(self) -> float:
        avg_beat_duration = np.mean(np.diff(self.beats))
        bpm = 60 / avg_beat_duration

        return bpm
    
    def convert_splited_beats_into_eighths(self: TStructure) -> TStructure:
        eighth_beats = []
        eighth_beat_positions = []
        beats = self.beats
        beat_positions = self.beat_positions
        for i in range(len(beats) - 1):
            beat_start = beats[i]
            beat_end = beats[i + 1]
            # 4分音符の開始ビート
            eighth_beats.append(beat_start)
            eighth_beat_positions.append(beat_positions[i])
            # その4分音符の中点を追加（8分音符に相当）
            eighth_beats.append(round(beat_start + (beat_end - beat_start) / 2, 2))
            eighth_beat_positions.append(beat_positions[i] + 0.5)
    
        # 最後の4分音符のビートも追加
        eighth_beats.append(beats[-1])
        eighth_beat_positions.append(beat_positions[-1])
    
        return Structure(bpm=self.bpm, beats=eighth_beats, downbeats=self.downbeats, beat_positions=eighth_beat_positions, segments=self.segments)