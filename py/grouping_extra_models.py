import os
import yaml
import folder_paths
from server import PromptServer
from aiohttp import web

# JSに渡すためのマッピングデータ
# { "model_name": "yaml_key_name" }
MODEL_SOURCE_MAP = {}

# 逆引き用辞書 { "絶対パス": "yamlのセクションキー" }
BASE_PATH_TO_LABEL = {}

# 既存のキャッシュを走査してマッピングを構築する関数
def sync_existing_cache_to_metadata():
    # filename_list_cache は { folder_name: (list_of_files, dict_metadata, timestamp) }
    for folder_name, cache_entry in folder_paths.filename_list_cache.items():
        MODEL_SOURCE_MAP[folder_name] = {}
            
        # タプルの第0要素がファイル名のリストです
        files = cache_entry[0] 
        
        for f in files:
            full_path = folder_paths.get_full_path(folder_name, f)
            if full_path:
                label = get_label_for_file(full_path)
                # 空文字（Default/Standard）か、_managed_ 除去済みのラベルを格納
                MODEL_SOURCE_MAP[folder_name][f] = label.removeprefix("_managed_")

def load_extra_path_config():
    # ComfyUI標準の場所にあるyamlを探す
    comfy_root = os.path.abspath(os.path.dirname(os.path.realpath(folder_paths.__file__ or "")))
    config_path = os.path.join(comfy_root, "extra_model_paths.yaml")
    if not os.path.exists(config_path):
        return

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            for label, contents in config.items():
                if isinstance(contents, dict) and "base_path" in contents:
                    # 絶対パスに変換して保存
                    abs_base = os.path.abspath(contents["base_path"])
                    BASE_PATH_TO_LABEL[abs_base] = label
    except Exception as e:
        print(f"Error loading extra config: {e}")

def normalize_label(label):
    label = label.removeprefix("_managed_") # For personal reason
    return label


# get_filename_list_ のフック内でこれを利用
def get_label_for_file(full_path):
    if not full_path: return ""
    
    # ファイルのパスが、どのベースパス配下にあるかチェック
    for base_path, label in BASE_PATH_TO_LABEL.items():
        if full_path.startswith(base_path):
            return label
    return ""

orig_get_list_ = folder_paths.get_filename_list_

def patched_get_filename_list_(folder_name):
    result = orig_get_list_(folder_name)
    
    # folder_names_and_paths は { folder_name: ([paths], {extensions}) } という構造
    # extra_model_paths.yaml の内容は、paths の中に含まれている
    
    # 常に初期化（現在のスキャン結果で上書き）
    MODEL_SOURCE_MAP[folder_name] = {}

    # yamlのセクション名を取得したい場合
    # 実際には folder_paths.base_path や models_dir 等と比較して
    # どのエントリーに属するかを判定するロジックが必要
    for f in result[0]:
        full_path = folder_paths.get_full_path(folder_name, f)
        if full_path:
            # 各ファイルがどの定義にあるかを逆引き
            source_label = get_label_for_file(full_path)
            MODEL_SOURCE_MAP[folder_name][f] = normalize_label(source_label)
            # print(MODEL_SOURCE_MAP[folder_name][f])
    return result


# 起動時に一度だけ実行
# A. YAMLを読んで BASE_PATH_TO_LABEL を作る
load_extra_path_config()
# B. 既存キャッシュを走査して MODEL_SOURCE_MAP を埋める
sync_existing_cache_to_metadata()
# C. 関数をパッチする
folder_paths.get_filename_list_ = patched_get_filename_list_

# JS側から取得するためのエンドポイント
@PromptServer.instance.routes.get("/hetima_stand/model_metadata")
async def get_sources(request):
    return web.json_response(MODEL_SOURCE_MAP)
