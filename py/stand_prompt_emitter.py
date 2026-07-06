from server import PromptServer


class StandPromptEmitter:
    """受け取った文字列を指定ノードのテキストウィジェットへ送るノード。"""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
                "target_node_id": ("INT", {"default": 0, "min": 0}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "emit"
    CATEGORY = "ComfyStand/text"
    OUTPUT_NODE = True

    def emit(self, text, target_node_id, unique_id=None):
        PromptServer.instance.send_sync(
            "comfystand.prompt_emitted",
            {
                "source_node_id": unique_id,
                "target_node_id": int(target_node_id),
                "text": "" if text is None else str(text),
            },
        )
        return ()


NODE_CLASS_MAPPINGS = {
    "StandPromptEmitter": StandPromptEmitter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StandPromptEmitter": "Stand Prompt Emitter",
}
