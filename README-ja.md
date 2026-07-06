# ComfyStand

ComfyUIのカスタムノードなどです。

## インストール

`git clone` などして `custom_nodes` に入れてください。追加の pip パッケージは不要です。

## Stand Multi LoRA Loader

LoRA ローダーです。指定したフォルダ内の LoRA ファイルを一覧表示して、ロードするものを選べます。Multi と Single のモードがあり、Multi ではチェックボックスで複数選択でき、Single ではラジオボタンでひとつだけ選べます。

適用強度は「Globalの値 x LoRAごとの値」です。

`lora_names` は LoRA ファイルの名前を出力します。\
`trigger_word` はプロンプト用のテキストを出力します。LoRAファイルと同名の `.txt` ファイルに書かれている内容を読み込みます。フォールバックとして `trigger.txt` という名前のファイルがあれば読み込みます。フォルダ内の LoRA すべてで同じトリガーワードを使いたいときに便利です。

Nodes 2.0 でも動くとは思いますが、表示が乱れます。

CLIPを含まない `Stand Multi LoRA Loader (Model Only)` と2つのノードがあります。

![Screenshot](https://raw.githubusercontent.com/hetima/ComfyStand/main/assets/multi_lora_loader.jpg)


## Stand Save Video

動画をProRes、H.264、H.265などのフォーマットで保存します。


## Stand Prompt Emitter

プロンプト生成ノード群（Generate Textなど）の終端に取り付けてMuteしておいてください。テキスト編集ノードのidを指定してください。常時Mute状態なのでメイン実行ボタンではされず、Applyを押したときだけ（Mute状態を保ったまま）実行され、テキスト編集ノードに結果を流し込みます。直接接続はしていないので編集可能です。


## Enable Grouping Extra Models

環境設定→Application Settings→Stand で設定を有効にすると使えるようになります。
各種モデルのポップアップを `extra_model_paths.yaml` で設定されたフォルダごとにグループ分けして分かりやすく表示します。[ComfyUI-manage_model_path](https://github.com/hetima/ComfyUI-manage_model_path) スクリプトを使用すると `extra_model_paths.yaml` を楽に管理できます。

Nodes 2.0 には対応していません。

![Screenshot](https://raw.githubusercontent.com/hetima/ComfyStand/main/assets/grouping_extra_models.jpg)


## ライセンス
MIT