"""Stand Load Video Segment - フルパス指定の動画をセグメント単位で読み込むローダー。

動画全体ではなく num_frames * segment_index フレーム目から num_frames 分だけを
IMAGE シーケンスとして返す（例: num_frames=100, segment_index=8 → 800〜899フレーム）。
video_path は input フォルダに依存しないフルパスで指定する。
あわせて実際に返したフレーム数 count、width/height、動画全体の総フレーム数、
num_frames で割った総セグメント数を出力する。
"""

import itertools
import os
from fractions import Fraction

import av
import numpy as np
import torch


class StandLoadVideoSegment:
    """動画の指定セグメントを IMAGE シーケンスとして返すノード。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": False,
                        "tooltip": "Full path to the video file (can be anywhere on this PC, not limited to the input folder).",
                    },
                ),
                "num_frames": (
                    "INT",
                    {
                        "default": 124,
                        "min": 1,
                        "max": 4096,
                        "step": 1,
                        "tooltip": "Number of frames to extract.",
                    },
                ),
                "segment_index": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 1000000,
                        "step": 1,
                        "tooltip": "0-based segment number. start frame = num_frames * segment_index (e.g. num_frames=100, segment_index=8 -> frames 800-899).",
                    },
                ),
                "padding": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Pad with black frames when fewer frames are available than requested.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "INT", "FLOAT", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        "IMAGE",
        "count",
        "fps",
        "width",
        "height",
        "total_frame_count",
        "total_segment_count",
    )
    FUNCTION = "load_video"
    CATEGORY = "ComfyStand/video"

    @classmethod
    def IS_CHANGED(cls, video_path, num_frames, segment_index, padding):
        path = _clean_path(video_path)
        try:
            stat = os.stat(path)
            signature = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            signature = None
        return (path, num_frames, segment_index, padding, signature)

    def load_video(self, video_path, num_frames, segment_index, padding):
        path = _clean_path(video_path)
        if not path:
            raise ValueError("video_path is empty")
        if not os.path.isfile(path):
            raise ValueError(f"video file not found: {path}")

        num_frames = int(num_frames)
        start = num_frames * int(segment_index)
        frames, fps, width, height = _decode_segment(path, start, num_frames)

        if frames:
            images = torch.from_numpy(np.stack(frames)).to(torch.float32).div_(255.0)
            height, width = int(images.shape[1]), int(images.shape[2])
        else:
            if width <= 0 or height <= 0:
                raise ValueError(f"cannot determine video dimensions: {path}")
            images = torch.zeros((0, height, width, 3), dtype=torch.float32)

        if padding and images.shape[0] < num_frames:
            missing = num_frames - images.shape[0]
            images = torch.cat(
                [images, torch.zeros((missing, height, width, 3))], dim=0
            )

        total_frames = _count_frames(path)
        # 最後のセグメントが num_frames に満たない場合も 1 セグメントとして数える
        # （padding=True で総フレーム数ちょうどまで segment_index を回せる）。
        total_segments = (total_frames + num_frames - 1) // num_frames

        # count は padding 後の実際のフレーム数。padding=False の最終セグメントのみ
        # num_frames より小さくなる（開始位置が終端を超えていれば 0）。
        return (
            images,
            int(images.shape[0]),
            float(fps),
            width,
            height,
            total_frames,
            total_segments,
        )


def _clean_path(video_path):
    """前後の空白と、Explorer の「パスのコピー」で付く引用符を剥がす。"""
    path = (video_path or "").strip()
    if len(path) >= 2 and path[0] == path[-1] and path[0] in "\"'":
        path = path[1:-1].strip()
    return path


def _decode_segment(path, start, wanted):
    """start フレーム目から wanted フレーム分を RGB uint8 配列のリストとして返す。

    キーフレームへの Seek + デコード破棄で start まで到達し、先頭からの全デコードを
    避ける。Seek やタイムスタンプ計算が使えないファイルでは先頭から順にデコードして
    フレーム番号でスキップする。戻り値は (frames, fps, width, height)。
    """
    container = av.open(path)
    try:
        stream = container.streams.video[0]
        try:
            stream.thread_type = "AUTO"
        except AttributeError:
            pass

        fps = stream.average_rate or stream.guessed_rate or Fraction(25, 1)
        width, height = int(stream.width), int(stream.height)

        skip = None
        if start > 0 and stream.time_base is not None:
            # pts は stream.start_time 起点の CFR を仮定して算出（VFR では多少ずれる）。
            target = (
                Fraction(stream.start_time or 0)
                + Fraction(start) / fps / stream.time_base
            )
            try:
                container.seek(int(target), stream=stream)
                skip = (
                    lambda frame: frame.pts is not None and Fraction(frame.pts) < target
                )
            except (av.FFmpegError, OSError):
                skip = None

        if skip is None:
            decoded = itertools.count()
            skip = lambda frame: next(decoded) < start

        frames = []
        for frame in container.decode(stream):
            if skip(frame):
                continue
            frames.append(frame.to_ndarray(format="rgb24"))
            if len(frames) >= wanted:
                break
        return frames, fps, width, height
    finally:
        container.close()


_FRAME_COUNT_CACHE = {}
_FRAME_COUNT_CACHE_LIMIT = 32


def _count_frames(path):
    """動画全体の総フレーム数を返す。

    コンテナヘッダの frames（mp4/mov では正確）を利用し、取れない場合のみ
    デコードせずパケットを数える（1パケット=1フレームのコンテナがほとんど）。
    結果は (パス, mtime, サイズ) でキャッシュし、segment_index を回しても
    毎回フルスキャンしない。
    """
    try:
        stat = os.stat(path)
        key = (os.path.abspath(path), stat.st_mtime_ns, stat.st_size)
        cached = _FRAME_COUNT_CACHE.get(key)
        if cached is not None:
            return cached
    except OSError:
        key = None

    container = av.open(path)
    try:
        stream = container.streams.video[0]
        total = int(stream.frames or 0)
        if total <= 0:
            total = sum(1 for _ in container.demux(stream))
    finally:
        container.close()

    if key is not None:
        if len(_FRAME_COUNT_CACHE) >= _FRAME_COUNT_CACHE_LIMIT:
            _FRAME_COUNT_CACHE.clear()
        _FRAME_COUNT_CACHE[key] = total
    return total


NODE_CLASS_MAPPINGS = {
    "StandLoadVideoSegment": StandLoadVideoSegment,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StandLoadVideoSegment": "Stand Load Video Segment",
}
