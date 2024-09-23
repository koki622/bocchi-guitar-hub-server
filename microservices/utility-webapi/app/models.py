import json
import os
from pathlib import Path
from typing import List
from fastapi import HTTPException
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
    
class Chord(BaseModel):
    time: float
    duration: float
    value: str

class AdjustedChord(Chord):
    was_adjusted: bool

    
class ChordList(JsonLoadableBase):
    chords: List[Chord]

class AdjustedChordList(JsonLoadableBase):
    adjusted_chords: List[AdjustedChord]

    def save_as_json_file(self, save_path: Path):
        json_data = self.model_dump_json()
        with open(save_path, 'w') as f:
            f.write(json_data)

class Segment(BaseModel):
    start: float
    end: float
    label: str

class Structure(JsonLoadableBase):
    bpm: int
    beats: List[float]
    downbeats: List[float]
    beat_positions: List[int]
    segments: List[Segment]
