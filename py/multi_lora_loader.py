import json
import os

import comfy.sd
import comfy.utils
import folder_paths
from aiohttp import web
from server import PromptServer


SUPPORTED_EXTENSIONS = {".safetensors", ".pt", ".ckpt", ".bin"}


def _is_lora_file(path):
    return os.path.splitext(path)[1].lower() in SUPPORTED_EXTENSIONS


def _resolve_lora_root(root_path):
    """引数のパスを優先し、空/無効なら ComfyUI の loras フォルダへフォールバックする。"""
    if root_path:
        resolved = os.path.abspath(os.path.expanduser(root_path))
        if os.path.isdir(resolved):
            return resolved

    for candidate in folder_paths.get_folder_paths("loras"):
        resolved = os.path.abspath(os.path.expanduser(candidate))
        if os.path.isdir(resolved):
            return resolved

    return ""


def _scan_lora_folder(root_path):
    root_path = _resolve_lora_root(root_path)
    if not root_path:
        return []

    files = []
    for current_root, _, names in os.walk(root_path):
        for name in names:
            if not _is_lora_file(name):
                continue

            full_path = os.path.join(current_root, name)
            relative_path = os.path.relpath(full_path, root_path).replace(os.sep, "/")
            files.append({
                "name": name,
                "relative_path": relative_path,
                "full_path": full_path,
                "trigger_word": _read_trigger_word(full_path),
            })

    return sorted(files, key=lambda item: item["relative_path"].lower())


def _read_text_file(path):
    if not os.path.isfile(path):
        return ""

    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with open(path, "r", encoding=encoding) as text_file:
                return text_file.read().strip()
        except UnicodeDecodeError:
            continue
    return ""


def _read_trigger_word(lora_path):
    folder = os.path.dirname(lora_path)
    base_name = os.path.splitext(os.path.basename(lora_path))[0]
    same_name_text = os.path.join(folder, f"{base_name}.txt")
    trigger_text = _read_text_file(same_name_text)
    if trigger_text:
        return trigger_text

    return _read_text_file(os.path.join(folder, "trigger.txt"))


@PromptServer.instance.routes.get("/hetima_stand/multi_lora_loader/list")
async def list_loras(request):
    path = request.query.get("path", "")
    return web.json_response({
        "root_path": _resolve_lora_root(path),
        "loras": _scan_lora_folder(path),
    })


class MultiLoraLoader:
    """フルパス指定フォルダから複数LoRAを読み込み、MODEL/CLIPへ順番に適用するノード。"""

    loaded_loras = {}

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "lora_state": ("STRING", {"default": "{}", "multiline": True}),
            },
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "lora_names", "trigger_word")
    FUNCTION = "load_loras"
    CATEGORY = "ComfyStand/loaders"

    def load_loras(self, model, clip, lora_state):
        return self._load_loras_impl(model, clip, lora_state, apply_clip=True)

    def _load_loras_impl(self, model, clip, lora_state, apply_clip=True):
        try:
            state = json.loads(lora_state or "{}")
        except json.JSONDecodeError:
            state = {}

        global_strength = float(state.get("global_strength", 1.0))
        lora_names = []
        trigger_words = []
        seen_trigger_words = set()
        selected_loras = state.get("loras", [])
        for lora in selected_loras:
            if not lora.get("enabled"):
                continue

            full_path = os.path.abspath(os.path.expanduser(lora.get("full_path", "")))
            strength = float(lora.get("strength", 1.0)) * global_strength
            if strength == 0 or not os.path.isfile(full_path) or not _is_lora_file(full_path):
                continue

            lora_names.append(os.path.splitext(os.path.basename(full_path))[0])
            # trigger_word = str(lora.get("trigger_word", "") or _read_trigger_word(full_path)).strip()
            trigger_word = str(lora.get("trigger_word", "")).strip()
            if trigger_word and trigger_word not in seen_trigger_words:
                trigger_words.append(trigger_word)
                seen_trigger_words.add(trigger_word)

            cached = self.loaded_loras.get(full_path)
            if cached is None:
                lora_data, metadata = comfy.utils.load_torch_file(
                    full_path,
                    safe_load=True,
                    return_metadata=True,
                )
                cached = (lora_data, metadata)
                self.loaded_loras[full_path] = cached

            lora_data, metadata = cached
            strength_clip = strength if apply_clip else 0
            model, clip = comfy.sd.load_lora_for_models(
                model,
                clip,
                lora_data,
                strength,
                strength_clip,
                lora_metadata=metadata,
            )

        return (model, clip, "+".join(lora_names), "\n".join(trigger_words))


class MultiLoraLoaderModelOnly(MultiLoraLoader):
    """複数LoRAをMODELのみに適用するノード。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "lora_state": ("STRING", {"default": "{}", "multiline": True}),
            },
        }

    RETURN_TYPES = ("MODEL", "STRING", "STRING")
    RETURN_NAMES = ("MODEL", "lora_names", "trigger_word")
    FUNCTION = "load_loras_model_only"
    CATEGORY = "ComfyStand/loaders"

    def load_loras_model_only(self, model, lora_state):
        model, _, lora_names, trigger_word = self._load_loras_impl(
            model,
            None,
            lora_state,
            apply_clip=False,
        )
        return (model, lora_names, trigger_word)


NODE_CLASS_MAPPINGS = {
    "ComfyStandMultiLoraLoader": MultiLoraLoader,
    "ComfyStandMultiLoraLoaderModelOnly": MultiLoraLoaderModelOnly,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ComfyStandMultiLoraLoader": "Stand Multi LoRA Loader",
    "ComfyStandMultiLoraLoaderModelOnly": "Stand Multi LoRA Loader (Model Only)",
}
