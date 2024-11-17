from datetime import datetime
from pydub import AudioSegment
from pathlib import Path
from typing import Literal


class AudioConversionService:
    SupportedFormats = Literal['mp3', 'ogg', 'wav']

    @staticmethod
    def convert_audiofile_to_format(input_files: list[Path], intput_file_extension: Literal['wav', 'mp3'], output_directory: Path, output_format: SupportedFormats) -> list[Path]:
        """音声ファイルを指定のフォーマットに変換します

        Args:
            input_files (list[Path]): 変換元のファイルのパス
            input_file_extension (Literal['wav', 'mp3']): 変換元のフォーマット
            output_directory (Path): 保存先のディレクトリのパス
            output_format (SupportedFormats): 変換先のフォーマット

        Returns:
            Path: 変換後のファイルのパス
        """
        output_files = []
        for file in input_files:
            print(file)
            if not file.exists() or not file.suffix == f'.{intput_file_extension}':
                raise FileNotFoundError(f"Input file must be a {intput_file_extension} file: {file}")
            output_file = output_directory / f'{file.stem}.{output_format}'
            output_files.append(output_file)

            if intput_file_extension == 'wav': 
                # WAVファイルをロード
                audio = AudioSegment.from_wav(file)
            elif intput_file_extension == 'mp3':
                # MP3ファイルをロード
                audio = AudioSegment.from_mp3(file)

            start_time = datetime.now()
            # 変換して保存
            audio.export(output_file, format=output_format)
            end_time = datetime.now()
            print(f"変換処理時間: {end_time - start_time} ")
        return output_files