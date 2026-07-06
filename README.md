# ComfyStand

<p align="center">English</a> | <a href="./README-ja.md">日本語</a></p>

Custom nodes for ComfyUI.

## Installation

Clone this repository into your `custom_nodes` folder (e.g. via `git clone`). No additional pip packages are required.

## Stand Multi LoRA Loader

A LoRA loader. It lists the LoRA files in a specified folder and lets you select which ones to load. There are two modes: **Multi** and **Single**. In Multi mode you can select multiple items via checkboxes, and in Single mode you select a single item via a radio button.

The applied strength is calculated as `Global strength × Per-LoRA strength`.

`lora_names` outputs the names of the LoRA files.\
`trigger_word` outputs text for prompts. It reads the content of a `.txt` file with the same name as the LoRA file. As a fallback, it reads a file named `trigger.txt` if it exists. This is useful when you want all LoRAs in a folder to share the same trigger word.

It should also work on Nodes 2.0, but the layout will look broken.

There are two nodes available: the standard one, and `Stand Multi LoRA Loader (Model Only)` which does not include CLIP.

![Screenshot](https://raw.githubusercontent.com/hetima/ComfyStand/main/assets/multi_lora_loader.jpg)

## Stand Save Video

Save the video in formats such as ProRes, H.264, or H.265.


## Stand Prompt Emitter

Attach this node to the end of your prompt-generation chain, such as after a Generate Text node, and set it to Mute. Enter the ID of the text-editing node you want to update.

The emitter stays muted during normal queue runs, so it will only execute when you press Apply. The generated text is then inserted into the target text-editing node without a direct connection, keeping the text editable.



## Enable Grouping Extra Models

Enable the setting under Settings → Application Settings → Stand to use this feature.
It groups the popups for various models by the folders configured in `extra_model_paths.yaml`, making them easier to read. The [ComfyUI-manage_model_path](https://github.com/hetima/ComfyUI-manage_model_path) script helps you manage `extra_model_paths.yaml` with ease.

Not compatible with Nodes 2.0.

![Screenshot](https://raw.githubusercontent.com/hetima/ComfyStand/main/assets/grouping_extra_models.jpg)


## License
MIT
