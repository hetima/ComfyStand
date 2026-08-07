import gc

import comfy.model_management as model_management
import torch


class StandUnloadModels:
    """読み込まれている全モデルとキャッシュを解放するノード。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "unload_models"
    CATEGORY = "ComfyStand/utils"

    def unload_models(self):
        print("Stand Unload Models:")
        print(" - Unloading all models...")
        model_management.unload_all_models()
        model_management.soft_empty_cache(True)

        try:
            print(" - Clearing cache...")
            gc.collect()
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()
        except Exception:
            print("   - Unable to clear cache")

        return ("unlaoded",)


NODE_CLASS_MAPPINGS = {
    "StandUnloadModels": StandUnloadModels,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StandUnloadModels": "Stand Unload Models",
}
