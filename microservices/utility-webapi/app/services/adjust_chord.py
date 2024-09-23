"""コードのタイミング調整モジュール。

このモジュールは、事前に定義されたビートに合わせてコードのタイミングを調整するための関数を提供します。
ビートに最も近い時間を見つけるための関数と、コードのタイミングを調整するための関数が含まれています。

関数:
    calculate_average_beat_interval(beat_times)
        全てのビート間のインターバルを計算します。
    
    closest_beat_time(time, beat_times, average_beat_interval):
        指定された時間に最も近いビートの時間を見つけます。

    adjust_chord_timing(beat_times, chords):
        コードのタイミングを最も近いビートに合わせて調整します。

使用例:
    ビートに合わせてコードのタイミングを調整する例:

    ```python
    beat_times = [3.11, 3.82, 4.48, 5.17, 5.86, 6.53, 7.23, 7.93, 8.62, 9.3]
    chords = ChordList([
        Chord(time = 0, duration = 3.07, value = 'N'),
        Chord(time = 3.07, duration = 1.39, value = "G#:min"),
        Chord(time = 4.46, duration = 1.39, value = "F#:maj"),
    ])
    adjusted_chords = adjust_chord_timing(beat_times, chords)
    print(adjusted_chords)
    ```

    上記のコードを実行すると、以下のような出力が得られます:

    ```python
    AdjustedChordList([
        AdjustedChord(time = 0, duration = 3.11, value = 'N'),
        AdjustedChord(time = 3.11, duration = 1.37, value = 'G#:min),
        AdjustedChord(time = 4.48, duration = 1.38, value = 'F#:maj)
    ])
    ```

    この結果は、各コードの開始時刻が最も近いビートに調整され、各コードの持続時間が次のコードの開始時刻またはビートまでの時間で計算されたことを示しています。
"""

from typing import List, Tuple

from app.models import AdjustedChord, AdjustedChordList, ChordList

def calculate_average_beat_interval(beat_times: List[float]) -> float:
    """全ビート間の平均インターバルを計算します。

    Args:
        beat_times (List[float]): ビートの時間のリスト。

    Returns:
        float: ビート間の平均インターバル
    """
    intervals = [beat_times[i+1] - beat_times[i] for i in range(len(beat_times) - 1)]
    return sum(intervals) / len(intervals)

def closest_beat_time(
        time: float, 
        beat_times: List[float], 
        average_beat_interval: float
) -> Tuple[float, bool]:
    """指定された時間に最も近いビートの時間を見つけ、補正結果を返します。
    指定の時間と最も近いビートの時間の差が全ビート間の平均インターバルよりも
    大きい場合は、補正結果ではなく、指定の時間をそのまま返します。

    Args:
        time (float): ビートと比較したい時間。
        beat_times (List[float]): ビートの時間のリスト。昇順にソートされている必要があります。
        average_beat_interval (float): 全ビート間の平均インターバル。

    Returns:
        Tuple[float, bool]: ビートの時間のリストの中で指定された時間に最も近いビートの時間と
        調整されたかどうかを示すフラグ。
        調整されなかった場合は元の時間を返し、Falseを返します。
    """
    closest_time = beat_times[0]
    min_diff = abs(closest_time - time)

    # 2番目以降のビートと比較
    for beat_time in beat_times[1:]:
        diff = abs(beat_time - time)
        
        # ビートが今までの最小値より小さい場合
        if diff < min_diff:
            closest_time = beat_time
            min_diff = diff
        # ビートが今までの最小値よりも大きい場合終了
        else:
            # ビートが平均ビート間隔よりも大きな誤差であれば補正しない
            if min_diff > average_beat_interval:
                return time, False 
            break
    return closest_time, True


def adjust_chord_time(
        beat_times: List[float], 
        chords: ChordList
) -> AdjustedChordList:
    """コードのタイミングを最も近いビートに合わせて調整します。

    Args:
        beat_times (List[float]): ビートの時間のリスト。
        chords (ChordList): コードの時間、持続時間、コード名を含むChordクラスのリスト。

    Returns:
        AdjustedChordList: 調整されたコードのタイミングと持続時間、コード名に加えて
        調整されたかどうかを示すブール値を含むAdjustedChordのリストを格納したAdjustedChordListを返します。
    """
    adjusted_chords = []
    remaining_beats = beat_times.copy() # 残りのビート

    # ビートの平均間隔を計算
    average_beat_interval = calculate_average_beat_interval(beat_times)

    for i, chord in enumerate(chords.chords):
        
        # コードの開始時刻を最も近いビートに合わせる
        adjusted_time, was_adjusted = closest_beat_time(chord.time, remaining_beats, average_beat_interval)

        # adjusted_time以下のビートをすべて削除
        remaining_beats = [beat for beat in remaining_beats if beat > adjusted_time]

        if i < len(chords.chords) - 1:
            # 次のコードの開始時刻を探す
            next_time, _ = closest_beat_time(chords.chords[i + 1].time, remaining_beats, average_beat_interval)
        else:
            # 最後のコードの場合、ビートリストの最大値を使用
            next_time = max(beat_times)

        # コードの時間の長さを計算
        adjusted_duration = round(next_time - adjusted_time, 2)

        adjusted_chords.append(AdjustedChord(
            time = adjusted_time,
            duration = adjusted_duration,
            value = chord.value,
            was_adjusted = was_adjusted
        ))
    return AdjustedChordList(adjusted_chords=adjusted_chords)

