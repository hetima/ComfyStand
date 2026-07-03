"""Stand Save Video - quality-tier video save for ComfyUI.

Ported from ComfyUI-SaveVideoHQ. (https://github.com/xergon/ComfyUI-SaveVideoHQ)
Uses the canonical comfy_api io.ComfyNode +
ui.PreviewVideo pattern (same as the built-in SaveVideo node) so the frontend
mounts an inline video player + download link after a successful save.
"""

import os
import logging
from fractions import Fraction

import av
import folder_paths

from comfy_api.latest import io, ui


log = logging.getLogger("StandSaveVideo")


# All presets are intra-only. Naming: <codec>_AllI_<subsampling>_<bitdepth>_<quality>.
# 10-bit pix_fmts use a uint16 RGB intermediate so float precision survives to the encoder.
PRESETS = {
    "ProRes_Proxy_4:2:2_10bit_(~45Mbps)":     {"codec": "prores_ks", "container": "mov", "pix_fmt": "yuv422p10le", "opts": {"profile": "0"}},
    "ProRes_LT_4:2:2_10bit_(~102Mbps)":       {"codec": "prores_ks", "container": "mov", "pix_fmt": "yuv422p10le", "opts": {"profile": "1"}},
    "ProRes_422_4:2:2_10bit_(~147Mbps)":      {"codec": "prores_ks", "container": "mov", "pix_fmt": "yuv422p10le", "opts": {"profile": "2"}},
    "ProRes_HQ_4:2:2_10bit_(~220Mbps)":       {"codec": "prores_ks", "container": "mov", "pix_fmt": "yuv422p10le", "opts": {"profile": "3"}},
    "ProRes_4444_4:4:4_12bit_(~330Mbps)":     {"codec": "prores_ks", "container": "mov", "pix_fmt": "yuv444p10le", "opts": {"profile": "4"}},
    "ProRes_4444_XQ_4:4:4_12bit_(~500Mbps)":  {"codec": "prores_ks", "container": "mov", "pix_fmt": "yuv444p10le", "opts": {"profile": "5"}},

    "x264_4:2:0_8bit_CRF23":  {"codec": "libx264", "container": "mp4", "pix_fmt": "yuv420p", "opts": {"crf": "23", "preset": "slow", "g": "240"}},
    "x264_4:2:0_8bit_CRF18":  {"codec": "libx264", "container": "mp4", "pix_fmt": "yuv420p", "opts": {"crf": "18", "preset": "slow", "g": "240"}},

    "x265_4:2:0_10bit_CRF28":     {"codec": "libx265", "container": "mp4", "pix_fmt": "yuv420p10le", "codec_tag": "hvc1", "opts": {"crf": "28", "preset": "medium", "tune": "ssim", "g": "240", "x265-params": "rc-lookahead=30"}},
    "x265_4:2:0_10bit_CRF24":     {"codec": "libx265", "container": "mp4", "pix_fmt": "yuv420p10le", "codec_tag": "hvc1", "opts": {"crf": "24", "preset": "medium", "tune": "ssim", "g": "240", "x265-params": "rc-lookahead=30"}},
    "x265_4:2:0_10bit_CRF18":     {"codec": "libx265", "container": "mp4", "pix_fmt": "yuv420p10le", "codec_tag": "hvc1", "opts": {"crf": "18", "preset": "medium", "tune": "ssim", "g": "240", "x265-params": "rc-lookahead=30"}},
    
    "FFV1_lossless_4:4:4_10bit":  {"codec": "ffv1", "container": "mkv", "pix_fmt": "yuv444p10le", "opts": {"level": "3", "g": "90", "coder": "1", "context": "1"}},

    # ----------------------------------------------------------------------
    # NVENC (hardware) presets - GPU encoder. ~5-10x faster than software.
    # Quality vs CRF: NVENC CQ ~= CRF + 4-6 at equivalent quality. Lower CQ here
    # to compensate. NVENC h264 is 8-bit only; HEVC + AV1 support 10-bit.
    # ----------------------------------------------------------------------
    # "H264_NVENC_AllI_4:2:0_8bit_CQ16":  {"codec": "h264_nvenc", "container": "mp4", "pix_fmt": "yuv420p", "opts": {"preset": "p7", "tune": "hq", "rc": "constqp", "qp": "16", "g": "1", "bf": "0", "profile": "high"}},
    # "H264_NVENC_AllI_4:4:4_8bit_CQ14":  {"codec": "h264_nvenc", "container": "mp4", "pix_fmt": "yuv444p", "opts": {"preset": "p7", "tune": "hq", "rc": "constqp", "qp": "14", "g": "1", "bf": "0", "profile": "high_444p"}},

    "H265_NVENC_4:2:0_10bit_CQ24":  {"codec": "hevc_nvenc", "container": "mp4", "pix_fmt": "p010le", "opts": {"preset": "p5", "rc": "vbr", "cq": "24", "g": "240", "rc-lookahead": "32", "spatial_aq": "1", "temporal_aq": "1", "aq-strength": "8"}},
    "H265_NVENC_4:2:0_10bit_CQ20":  {"codec": "hevc_nvenc", "container": "mp4", "pix_fmt": "p010le", "opts": {"preset": "p5", "rc": "vbr", "cq": "20", "g": "240", "rc-lookahead": "32", "spatial_aq": "1", "temporal_aq": "1", "aq-strength": "8"}},
    "H265_NVENC_4:2:0_10bit_CQ16":  {"codec": "hevc_nvenc", "container": "mp4", "pix_fmt": "p010le", "opts": {"preset": "p5", "rc": "vbr", "cq": "16", "g": "240", "rc-lookahead": "32", "spatial_aq": "1", "temporal_aq": "1", "aq-strength": "8"}},

    "Custom":  None,
}


H264_PROFILE = {
    "yuv420p": "high", "yuv422p": "high422", "yuv444p": "high444",
    "yuv420p10le": "high10", "yuv422p10le": "high422", "yuv444p10le": "high444",
}
H265_PROFILE = {
    "yuv420p": "main", "yuv422p": "main422-8", "yuv444p": "main444-8",
    "yuv420p10le": "main10", "yuv422p10le": "main422-10", "yuv444p10le": "main444-10",
}


_PRESET_NAMES = list(PRESETS.keys())
_CUSTOM_CODECS = ["libx264", "libx265", "prores_ks", "ffv1"]
_CONTAINERS = ["mp4", "mkv", "mov"]
_RATE_CONTROLS = ["crf", "bitrate", "lossless"]
_SPEEDS = ["medium", "slow", "slower", "veryslow", "placebo", "fast", "faster", "veryfast", "ultrafast"]
_PIX_FMTS = ["yuv444p10le", "yuv444p", "yuv422p10le", "yuv422p", "yuv420p10le", "yuv420p"]


class StandSaveVideo(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="StandSaveVideo",
            display_name="Stand Save Video",
            description="Save VIDEO with intra-only preset tiers (ProRes ladder, H.264 All-I, H.265 All-I, FFV1 lossless). Preset names spell out subsampling and bit depth. 10-bit presets use a 16-bit RGB pipeline so float precision reaches the encoder.",
            category="ComfyStand/video",
            inputs=[
                io.Video.Input("video"),
                io.String.Input("filename_prefix", default="video/ComfyUI"),
                io.Combo.Input("preset", options=_PRESET_NAMES, default="H264_AllI_4:2:2_10bit_CRF12",
                               tooltip="Preset format: <codec>_AllI_<subsampling>_<bitdepth>_<quality>. Pick Custom to use the manual widgets below."),
                io.Boolean.Input("includes_audio", default=False),
                io.Combo.Input("custom_codec", options=_CUSTOM_CODECS, default="libx264"),
                io.Combo.Input("custom_container", options=_CONTAINERS, default="mp4"),
                io.Combo.Input("custom_rate_control", options=_RATE_CONTROLS, default="crf"),
                io.Int.Input("custom_crf", default=12, min=0, max=51),
                io.Int.Input("custom_bitrate_mbps", default=80, min=1, max=2000),
                io.Combo.Input("custom_preset_speed", options=_SPEEDS, default="slow"),
                io.Boolean.Input("custom_all_intra", default=True),
                io.Combo.Input("custom_pix_fmt", options=_PIX_FMTS, default="yuv444p10le"),
            ],
            outputs=[],
            is_output_node=True,
        )

    @classmethod
    def execute(cls, video, filename_prefix, preset,
                includes_audio,
                custom_codec, custom_container, custom_rate_control,
                custom_crf, custom_bitrate_mbps, custom_preset_speed,
                custom_all_intra, custom_pix_fmt) -> io.NodeOutput:
        cfg = PRESETS.get(preset)
        if cfg is None:
            cfg = _build_custom_config(
                custom_codec, custom_container, custom_rate_control,
                custom_crf, custom_bitrate_mbps, custom_preset_speed,
                custom_all_intra, custom_pix_fmt,
            )

        codec = cfg["codec"]
        container = cfg["container"]
        pix_fmt = cfg["pix_fmt"]
        opts = cfg["opts"]
        codec_tag = cfg.get("codec_tag")

        comp = video.get_components()
        frames = comp.images
        audio = comp.audio if includes_audio else None
        fps = comp.frame_rate
        if not isinstance(fps, Fraction):
            fps = Fraction(float(fps)).limit_denominator(1000)

        output_dir = folder_paths.get_output_directory()
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, output_dir)
        os.makedirs(full_output_folder, exist_ok=True)
        out_filename = f"{filename}_{counter:05}_.{container}"
        out_path = os.path.join(full_output_folder, out_filename)

        outc = av.open(out_path, mode="w")
        try:
            video_stream = _prepare_video(outc, frames, fps, codec, opts, pix_fmt, codec_tag)
            audio_state = None
            if audio is not None:
                try:
                    audio_state = _prepare_audio(outc, audio, container)
                except Exception as e:
                    log.warning(f"audio setup failed: {e}; saving video-only")

            _encode_video(outc, video_stream, frames, pix_fmt)
            if audio_state is not None:
                try:
                    _encode_audio(outc, audio_state)
                except Exception as e:
                    log.warning(f"audio passthrough failed: {e}; saving video-only")
        finally:
            outc.close()

        size_mb = os.path.getsize(out_path) / 1e6
        log.info(f"StandSaveVideo wrote {out_path} ({size_mb:.1f} MB) preset={preset}")

        return io.NodeOutput(ui=ui.PreviewVideo([
            ui.SavedResult(out_filename, subfolder, io.FolderType.output),
        ]))


def _build_custom_config(codec, container, rate_control, crf, bitrate_mbps,
                         preset_speed, all_intra, pix_fmt):
    opts = {}
    if codec in ("libx264", "libx265"):
        opts["preset"] = preset_speed
        if rate_control == "lossless":
            if codec == "libx264":
                opts["qp"] = "0"
            else:
                opts["x265-params"] = "lossless=1"
        elif rate_control == "bitrate":
            opts["b"] = f"{bitrate_mbps}M"
            opts["maxrate"] = f"{int(bitrate_mbps * 1.5)}M"
            opts["bufsize"] = f"{bitrate_mbps * 2}M"
        else:
            opts["crf"] = str(crf)
        if codec == "libx264":
            opts["profile"] = H264_PROFILE.get(pix_fmt, "high")
        else:
            opts["profile"] = H265_PROFILE.get(pix_fmt, "main")
        if all_intra:
            opts["g"] = "1"
            opts["bf"] = "0"
            if codec == "libx264":
                opts["x264-params"] = "keyint=1:scenecut=0"
            else:
                existing = opts.get("x265-params", "")
                extra = "keyint=1:no-open-gop=1:bframes=0:tune=grain:deblock=-3,-3"
                opts["x265-params"] = f"{existing}:{extra}" if existing else extra
    elif codec == "prores_ks":
        opts["profile"] = "5" if "444" in pix_fmt else "3"
    elif codec == "ffv1":
        opts.update({"level": "3", "coder": "1", "context": "1", "g": "1"})
    return {"codec": codec, "container": container, "pix_fmt": pix_fmt, "opts": opts}


def _prepare_video(outc, frames, fps, codec, opts, pix_fmt, codec_tag=None):
    n, h, w, c = frames.shape
    if c != 3:
        raise ValueError(f"expected 3 channels (RGB), got {c}")
    stream = outc.add_stream(codec, rate=fps)
    stream.width = int(w)
    stream.height = int(h)
    stream.pix_fmt = pix_fmt
    stream.time_base = Fraction(1, int(fps * 1000))
    stream.options = opts
    if codec_tag is not None:
        _set_codec_tag(stream, codec_tag)
    return stream


def _set_codec_tag(stream, tag):
    try:
        stream.codec_context.codec_tag = tag
    except TypeError:
        stream.codec_context.codec_tag = int.from_bytes(tag.encode("ascii"), "little")


def _encode_video(outc, stream, frames, pix_fmt):
    is_high_bit = ("10le" in pix_fmt) or ("12le" in pix_fmt) or ("16le" in pix_fmt) or (pix_fmt == "p010le")
    if is_high_bit:
        arr = (frames.cpu().numpy() * 65535.0).clip(0, 65535).astype("uint16")
        for f in arr:
            frame = av.VideoFrame.from_ndarray(f, format="rgb48le")
            for packet in stream.encode(frame):
                outc.mux(packet)
    else:
        arr = (frames.cpu().numpy() * 255.0).clip(0, 255).astype("uint8")
        for f in arr:
            frame = av.VideoFrame.from_ndarray(f, format="rgb24")
            for packet in stream.encode(frame):
                outc.mux(packet)

    for packet in stream.encode():
        outc.mux(packet)


def _prepare_audio(outc, audio, container):
    wf = audio["waveform"]
    sr = int(audio["sample_rate"])
    if wf is None or wf.numel() == 0:
        return None

    a_codec = "aac"
    if container == "mkv":
        a_codec = "flac"
    elif container == "mov":
        a_codec = "pcm_s16le"

    waveform = wf[0].cpu()
    layout = "mono" if waveform.shape[0] == 1 else "stereo"
    a_stream = outc.add_stream(a_codec, rate=sr, layout=layout)
    return a_stream, waveform, sr, layout


def _encode_audio(outc, audio_state):
    a_stream, waveform, sr, layout = audio_state

    # Match ComfyUI's AudioSaveHelper: non-planar float ("flt"), pts=0, and let
    # the codec pick its own time_base. Forcing a stream time_base on a muxed
    # audio stream inside a video container trips a divide-by-zero inside
    # FFmpeg's native rate/timing math on some encoders (aac/pcm_s16le).

    a_frame = av.AudioFrame.from_ndarray(
        waveform.movedim(0, 1).reshape(1, -1).float().numpy(),
        format="flt",
        layout=layout,
    )
    a_frame.sample_rate = sr
    a_frame.pts = 0

    outc.mux(a_stream.encode(a_frame))
    outc.mux(a_stream.encode(None))  # flush


# Standard ComfyUI registration. StandSaveVideo is an io.ComfyNode subclass which
# the loader recognizes; it gets wired through the new comfy_api pipeline so
# the io.NodeOutput(ui=ui.PreviewVideo(...)) return shape is honored by the
# frontend.
NODE_CLASS_MAPPINGS = {"StandSaveVideo": StandSaveVideo}
NODE_DISPLAY_NAME_MAPPINGS = {"StandSaveVideo": "Stand Save Video"}
