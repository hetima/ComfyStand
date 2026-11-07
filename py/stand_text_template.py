import re

class AnyType(str):
    """A special class that is always equal in not equal comparisons. Credit to pythongosssss"""
    def __ne__(self, __value: object) -> bool:
        return False

any_type = AnyType("*")

class StandTextTemplate:

    CATEGORY = "ComfyStand/utils"
    DESCRIPTION = "Builds a text and return one includes placeholder replacements."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": "$1", "tooltip": 'can include "$1", "$2", "$3" and "$4"'}),
            },
            "optional": {
                "$1": (any_type, {"multiline": False, "default": "", "forceInput": True, "tooltip": 'replace "$1" with this value'}),
                "$2": (any_type, {"multiline": False, "default": "", "forceInput": True, "tooltip": 'replace "$2" with this value'}),
                "$3": (any_type, {"multiline": False, "default": "", "forceInput": True, "tooltip": 'replace "$3" with this value'}),
                "$4": (any_type, {"multiline": False, "default": "", "forceInput": True, "tooltip": 'replace "$4" with this value'}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("STRING",)
    OUTPUT_TOOLTIPS = ("text",)
    OUTPUT_NODE = True
    FUNCTION = "execute"
    
    def to_storing(self, val):
        if isinstance(val, str) and len(val) > 0:
            return val
        if isinstance(val, (int, float, bool)):
            return str(val)
        return ""
    
    def execute(self, **kwargs):
        text = kwargs["text"]
        if not text:
            return ""
        
        s1 = self.to_storing(kwargs.get("$1", ""))
        s2 = self.to_storing(kwargs.get("$2", ""))
        s3 = self.to_storing(kwargs.get("$3", ""))
        s4 = self.to_storing(kwargs.get("$4", ""))
        mapping = {"$1": s1, "$2": s2, "$3": s3, "$4": s4,}
        
        pattern = re.compile("|".join(re.escape(k) for k in mapping.keys()))
        text = pattern.sub(lambda m: mapping[m.group(0)], text)
        
        return (text,)

NODE_CLASS_MAPPINGS = {
    "StandTextTemplate": StandTextTemplate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StandTextTemplate": "Stand Text Template",
}
