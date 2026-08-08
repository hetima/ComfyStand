import torch


class StandPadAudio:
    """音声の先頭と末尾へ指定秒数の無音を追加するノード。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("AUDIO",),
                "pad_start_seconds": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 3600.0, "step": 0.001},
                ),
                "pad_end_seconds": (
                    "FLOAT",
                    {"default": 0.0, "min": 0.0, "max": 3600.0, "step": 0.001},
                ),
            },
        }

    RETURN_TYPES = ("AUDIO",)
    FUNCTION = "pad_audio"
    CATEGORY = "ComfyStand/audio"

    def pad_audio(self, audio, pad_start_seconds, pad_end_seconds):
        waveform = audio["waveform"]
        sample_rate = audio["sample_rate"]
        parts = []

        start_samples = round(float(pad_start_seconds) * sample_rate)
        if start_samples:
            parts.append(waveform.new_zeros((*waveform.shape[:-1], start_samples)))

        parts.append(waveform)

        end_samples = round(float(pad_end_seconds) * sample_rate)
        if end_samples:
            parts.append(waveform.new_zeros((*waveform.shape[:-1], end_samples)))

        return ({"waveform": torch.cat(parts, dim=-1), "sample_rate": sample_rate},)


NODE_CLASS_MAPPINGS = {
    "StandPadAudio": StandPadAudio,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StandPadAudio": "Stand Pad Audio",
}
