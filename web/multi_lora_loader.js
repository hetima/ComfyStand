import { app } from "../../scripts/app.js";

const NODE_NAMES = new Set([
    "ComfyStandMultiLoraLoader",
    "ComfyStandMultiLoraLoaderModelOnly",
]);
const STYLE_ID = "comfystand-multi-lora-style";
const DEFAULT_STATE = { root_path: "", mode: "multi", global_strength: 1, loras: [] };
const MIN_WIDGET_HEIGHT = 180;
const MAX_WIDGET_HEIGHT = 2000;
const DEFAULT_NODE_WIDTH = 460;

const STYLES = `
.cstand-mlora {
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 5px;
    width: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 6px;
    font-family: system-ui, sans-serif;
    font-size: 12px;
    background: #1a1a1a;
    border-radius: 4px;
    color: #ddd;
}

.cstand-mlora * {
    box-sizing: border-box;
}

.cstand-mlora-toolbar {
    display: flex;
    gap: 5px;
    align-items: center;
    min-width: 0;
}

.cstand-mlora-path {
    flex: 1;
    min-width: 0;
    height: 26px;
    padding: 4px 6px;
    background: #333;
    color: #fff;
    border: 1px solid #555;
    border-radius: 4px;
    outline: none;
    font-size: 12px;
}

.cstand-mlora-path:hover,
.cstand-mlora-path:focus {
    border-color: #777;
}

.cstand-mlora-btn {
    height: 26px;
    padding: 4px 10px;
    background: #444;
    color: #fff;
    border: 1px solid #555;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
    font-size: 12px;
    transition: background 0.15s, border-color 0.15s, opacity 0.15s;
}

.cstand-mlora-btn:hover {
    background: #555;
    border-color: #777;
}

.cstand-mlora-btn:disabled {
    cursor: wait;
    opacity: 0.65;
}

.cstand-mlora-mode {
    display: flex;
    gap: 3px;
    padding: 3px;
    background: #252525;
    border: 1px solid #383838;
    border-radius: 4px;
}

.cstand-mlora-controls {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 6px;
    align-items: center;
}

.cstand-mlora-mode-btn {
    flex: 1;
    height: 24px;
    padding: 3px 8px;
    background: #333;
    color: #aaa;
    border: 1px solid #444;
    border-radius: 3px;
    cursor: pointer;
    font-weight: 700;
    font-size: 12px;
    letter-spacing: 0;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.cstand-mlora-mode-btn:hover {
    background: #3a3a3a;
    color: #fff;
}

.cstand-mlora-mode-btn.selected {
    background: #4a7c4e;
    border-color: #5a9c5e;
    color: #fff;
}

.cstand-mlora-global {
    display: grid;
    grid-template-columns: auto auto;
    gap: 5px;
    align-items: center;
    white-space: nowrap;
}

.cstand-mlora-global-label {
    color: #aaa;
    font-size: 11px;
    font-weight: 700;
}

.cstand-mlora-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding-right: 2px;
}

.cstand-mlora-empty,
.cstand-mlora-error {
    padding: 14px 6px;
    text-align: center;
    color: #888;
}

.cstand-mlora-error {
    color: #e88;
}

.cstand-mlora-category {
    background: #2a2a2a;
    border-radius: 4px;
    overflow: hidden;
}

.cstand-mlora-category-header {
    display: flex;
    align-items: center;
    min-height: 26px;
    padding: 4px 8px;
    background: #333;
    cursor: pointer;
    user-select: none;
}

.cstand-mlora-category-header:hover {
    background: #3a3a3a;
}

.cstand-mlora-arrow {
    width: 12px;
    margin-right: 6px;
    color: #aaa;
    transition: transform 0.15s;
}

.cstand-mlora-category.open > .cstand-mlora-category-header .cstand-mlora-arrow {
    transform: rotate(90deg);
}

.cstand-mlora-category-name {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #ddd;
    font-weight: 700;
}

.cstand-mlora-category-count {
    color: #888;
    font-size: 10px;
    margin-left: 6px;
}

.cstand-mlora-category-content {
    display: none;
    flex-direction: column;
    gap: 2px;
    padding: 4px;
    background: #252525;
}

.cstand-mlora-category.open > .cstand-mlora-category-content {
    display: flex;
}

.cstand-mlora-row {
    display: grid;
    grid-template-columns: 16px minmax(0, 1fr) auto;
    gap: 6px;
    align-items: center;
    min-height: 26px;
    padding: 2px 5px;
    background: #444;
    color: #ccc;
    border: 1px solid #555;
    border-radius: 3px;
    transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.cstand-mlora-row:hover {
    background: #555;
    border-color: #777;
    color: #fff;
}

.cstand-mlora-row.selected {
    background: #4a7c4e;
    border-color: #5a9c5e;
    color: #fff;
}

.cstand-mlora-check {
    width: 13px;
    height: 13px;
    margin: 0;
    accent-color: #5a9c5e;
}

.cstand-mlora-name {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    cursor: pointer;
}

.cstand-mlora-strength {
    display: grid;
    grid-template-columns: 20px 42px 20px;
    gap: 2px;
    align-items: center;
}

.cstand-mlora-step {
    width: 20px;
    height: 20px;
    padding: 0;
    background: #333;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 3px;
    cursor: pointer;
    font-size: 11px;
    line-height: 1;
}

.cstand-mlora-step:hover {
    background: #555;
    border-color: #777;
    color: #fff;
}

.cstand-mlora-number {
    width: 42px;
    height: 20px;
    padding: 0 2px;
    background: #333;
    color: #fff;
    border: 1px solid #555;
    border-radius: 3px;
    text-align: center;
    outline: none;
    font-size: 11px;
}

.cstand-mlora-number:hover,
.cstand-mlora-number:focus {
    border-color: #777;
}

.cstand-mlora-number::-webkit-outer-spin-button,
.cstand-mlora-number::-webkit-inner-spin-button {
    margin: 0;
    -webkit-appearance: none;
}

.cstand-mlora-number {
    -moz-appearance: textfield;
    appearance: textfield;
}
`;

function clampStrength(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return 1;
    return Math.max(0, Math.min(2, Math.round(number * 100) / 100));
}

function parseState(value) {
    try {
        const parsed = JSON.parse(value || "{}");
        return {
            ...DEFAULT_STATE,
            ...parsed,
            loras: Array.isArray(parsed.loras) ? parsed.loras : [],
        };
    } catch {
        return { ...DEFAULT_STATE };
    }
}

function ensureStyle() {
    const style = document.getElementById(STYLE_ID) || document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = STYLES;
    if (!style.parentElement) {
        document.head.appendChild(style);
    }
}

function hideWidget(widget) {
    if (!widget) return;
    widget.type = "hidden";
    widget.hidden = true;
    widget.disabled = true;
    widget.computeSize = () => [1, 1];
    widget.draw = () => {};
    widget.serializeValue = () => widget.value;
}

function syncLoraRows(node) {
    const state = getState(node);
    const enabledPaths = new Set(
        state.loras.filter((lora) => lora.enabled).map((lora) => lora.relative_path),
    );
    const inputType = state.mode === "single" ? "radio" : "checkbox";
    node.comfystandMultiLoraRoot?.querySelectorAll(".cstand-mlora-row").forEach((row) => {
        const relativePath = row.dataset.relativePath;
        const enabled = enabledPaths.has(relativePath);
        row.classList.toggle("selected", enabled);
        const input = row.querySelector(".cstand-mlora-check");
        if (input) {
            input.type = inputType;
            input.checked = enabled;
        }
    });
}

function getState(node) {
    node.comfystandStateWidget = node.comfystandStateWidget || node.widgets?.find((widget) => widget.name === "lora_state");
    return parseState(node.comfystandStateWidget?.value);
}

function setState(node, state) {
    if (state.mode === "single") {
        let selected = false;
        state.loras = state.loras.map((lora) => {
            if (!lora.enabled) return lora;
            if (selected) return { ...lora, enabled: false };
            selected = true;
            return lora;
        });
    }
    node.comfystandStateWidget.value = JSON.stringify(state);
    node.setDirtyCanvas(true, true);
}

function mergeLoras(oldLoras, newLoras) {
    const oldByRelativePath = new Map(oldLoras.map((lora) => [lora.relative_path, lora]));
    return newLoras.map((lora) => {
        const old = oldByRelativePath.get(lora.relative_path);
        return {
            ...lora,
            enabled: Boolean(old?.enabled),
            strength: clampStrength(old?.strength ?? 1),
        };
    });
}

function createTree(loras) {
    const root = { name: "", path: "", folders: new Map(), files: [] };
    for (const lora of loras) {
        const parts = lora.relative_path.split("/");
        let current = root;
        for (const folder of parts.slice(0, -1)) {
            const path = current.path ? `${current.path}/${folder}` : folder;
            if (!current.folders.has(folder)) {
                current.folders.set(folder, { name: folder, path, folders: new Map(), files: [] });
            }
            current = current.folders.get(folder);
        }
        current.files.push(lora);
    }
    return root;
}

function countFiles(tree) {
    let count = tree.files.length;
    for (const child of tree.folders.values()) {
        count += countFiles(child);
    }
    return count;
}

app.registerExtension({
    name: "hetima.multi_lora_loader",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!NODE_NAMES.has(nodeData.name)) return;

        ensureStyle();

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            originalOnNodeCreated?.apply(this, arguments);
            ensureMultiLoraUi(this);
        };

        const originalConfigure = nodeType.prototype.configure;
        nodeType.prototype.configure = function () {
            originalConfigure?.apply(this, arguments);
            ensureMultiLoraUi(this);
            renderMultiLoraUi(this);
        };
    },
});

function ensureMultiLoraUi(node) {
    ensureStyle();
    node.serialize_widgets = true;
    node.comfystandStateWidget = node.widgets?.find((widget) => widget.name === "lora_state");
    hideWidget(node.comfystandStateWidget);
    node.comfystandExpandedFolders = node.comfystandExpandedFolders || new Set();

    if (node.comfystandMultiLoraRoot && node.widgets?.some((widget) => widget.name === "multi_lora_ui")) {
        return;
    }

    const root = document.createElement("div");
    root.className = "cstand-mlora";
    node.comfystandMultiLoraRoot = root;

    node.addDOMWidget("multi_lora_ui", "custom", root, {
        hideOnZoom: false,
        getMinHeight: () => MIN_WIDGET_HEIGHT,
        getMaxHeight: () => MAX_WIDGET_HEIGHT,
    });

    node.setSize([
        Math.max(DEFAULT_NODE_WIDTH, node.size?.[0] || DEFAULT_NODE_WIDTH),
        node.size?.[1] || 450,
    ]);
    renderMultiLoraUi(node);
}

async function reloadLoras(node, showError) {
    const state = getState(node);
    const response = await fetch(`/hetima_stand/multi_lora_loader/list?path=${encodeURIComponent(state.root_path)}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    setState(node, {
        ...state,
        root_path: data.root_path || state.root_path,
        loras: mergeLoras(state.loras, data.loras || []),
    });
    showError("");
    renderMultiLoraUi(node);
}

function renderMultiLoraUi(node) {
    const root = node.comfystandMultiLoraRoot;
    if (!root) return;

    const state = getState(node);
    root.innerHTML = "";

    const toolbar = document.createElement("div");
    toolbar.className = "cstand-mlora-toolbar";

    const pathInput = document.createElement("input");
    pathInput.className = "cstand-mlora-path";
    pathInput.value = state.root_path || "";
    pathInput.placeholder = "LoRA folder full path";
    pathInput.addEventListener("change", () => {
        setState(node, { ...getState(node), root_path: pathInput.value });
    });
    toolbar.appendChild(pathInput);

    const reloadButton = document.createElement("button");
    reloadButton.className = "cstand-mlora-btn";
    reloadButton.textContent = "Reload";
    toolbar.appendChild(reloadButton);
    root.appendChild(toolbar);

    const controls = document.createElement("div");
    controls.className = "cstand-mlora-controls";

    const mode = document.createElement("div");
    mode.className = "cstand-mlora-mode";
    for (const modeName of ["multi", "single"]) {
        const button = document.createElement("button");
        button.className = "cstand-mlora-mode-btn";
        button.classList.toggle("selected", state.mode === modeName);
        button.textContent = modeName === "multi" ? "Multi" : "Single";
        button.addEventListener("click", () => {
            setState(node, { ...getState(node), mode: modeName });
            renderMultiLoraUi(node);
        });
        mode.appendChild(button);
    }
    controls.appendChild(mode);

    const globalStrength = createGlobalStrengthControl(node, state);
    controls.appendChild(globalStrength);
    root.appendChild(controls);

    const list = document.createElement("div");
    list.className = "cstand-mlora-list";
    root.appendChild(list);

    const showError = (message) => {
        if (!message) return;
        list.innerHTML = "";
        const error = document.createElement("div");
        error.className = "cstand-mlora-error";
        error.textContent = message;
        list.appendChild(error);
    };

    reloadButton.addEventListener("click", async () => {
        setState(node, { ...getState(node), root_path: pathInput.value });
        reloadButton.disabled = true;
        reloadButton.textContent = "...";
        try {
            await reloadLoras(node, showError);
        } catch (error) {
            console.error("[ComfyStand] Failed to reload LoRAs:", error);
            showError(`Load error: ${error.message}`);
        } finally {
            reloadButton.disabled = false;
            reloadButton.textContent = "reload";
        }
    });

    if (!state.loras.length) {
        const empty = document.createElement("div");
        empty.className = "cstand-mlora-empty";
        empty.textContent = "Click reload to load LoRAs";
        list.appendChild(empty);
        return;
    }

    const tree = createTree(state.loras);
    for (const lora of tree.files) {
        list.appendChild(createLoraRow(node, lora));
    }
    for (const folder of tree.folders.values()) {
        list.appendChild(createCategory(node, folder));
    }
}

function createGlobalStrengthControl(node, state) {
    const container = document.createElement("div");
    container.className = "cstand-mlora-global";

    const label = document.createElement("div");
    label.className = "cstand-mlora-global-label";
    label.textContent = "Global:";
    container.appendChild(label);

    const strength = document.createElement("div");
    strength.className = "cstand-mlora-strength";

    const dec = document.createElement("button");
    dec.className = "cstand-mlora-step";
    dec.textContent = "-";
    strength.appendChild(dec);

    const number = document.createElement("input");
    number.className = "cstand-mlora-number";
    number.type = "number";
    number.min = "0";
    number.max = "2";
    number.step = "0.05";
    number.value = clampStrength(state.global_strength).toFixed(2);
    number.addEventListener("focus", () => number.select());
    strength.appendChild(number);

    const inc = document.createElement("button");
    inc.className = "cstand-mlora-step";
    inc.textContent = "+";
    strength.appendChild(inc);

    const updateStrength = (value) => {
        const globalStrength = clampStrength(value);
        setState(node, { ...getState(node), global_strength: globalStrength });
        number.value = globalStrength.toFixed(2);
    };
    dec.addEventListener("click", () => updateStrength(Number(number.value) - 0.05));
    inc.addEventListener("click", () => updateStrength(Number(number.value) + 0.05));
    number.addEventListener("change", () => updateStrength(number.value));

    container.appendChild(strength);
    return container;
}

function createCategory(node, tree) {
    const expanded = node.comfystandExpandedFolders.has(tree.path);
    const category = document.createElement("div");
    category.className = "cstand-mlora-category";
    category.classList.toggle("open", expanded);

    const header = document.createElement("div");
    header.className = "cstand-mlora-category-header";

    const arrow = document.createElement("span");
    arrow.className = "cstand-mlora-arrow";
    arrow.textContent = ">";
    header.appendChild(arrow);

    const name = document.createElement("span");
    name.className = "cstand-mlora-category-name";
    name.textContent = tree.name;
    name.title = tree.path;
    header.appendChild(name);

    const count = document.createElement("span");
    count.className = "cstand-mlora-category-count";
    count.textContent = `(${countFiles(tree)})`;
    header.appendChild(count);

    header.addEventListener("click", () => {
        const isOpen = category.classList.toggle("open");
        if (!isOpen) {
            node.comfystandExpandedFolders.delete(tree.path);
        } else {
            node.comfystandExpandedFolders.add(tree.path);
        }
        node.setDirtyCanvas(true, true);
    });
    category.appendChild(header);

    const content = document.createElement("div");
    content.className = "cstand-mlora-category-content";
    for (const lora of tree.files) {
        content.appendChild(createLoraRow(node, lora));
    }
    for (const folder of tree.folders.values()) {
        content.appendChild(createCategory(node, folder));
    }
    category.appendChild(content);

    return category;
}

function createLoraRow(node, lora) {
    const state = getState(node);
    const row = document.createElement("div");
    row.className = "cstand-mlora-row";
    row.dataset.relativePath = lora.relative_path;
    row.classList.toggle("selected", Boolean(lora.enabled));

    const check = document.createElement("input");
    check.type = state.mode === "single" ? "radio" : "checkbox";
    check.name = `cstand-mlora-${node.id || "new"}`;
    check.className = "cstand-mlora-check";
    check.checked = Boolean(lora.enabled);
    check.addEventListener("change", () => {
        const next = getState(node);
        next.loras = next.loras.map((item) => {
            if (item.relative_path === lora.relative_path) {
                return { ...item, enabled: check.checked };
            }
            if (next.mode === "single" && check.checked) {
                return { ...item, enabled: false };
            }
            return item;
        });
        setState(node, next);
        syncLoraRows(node);
    });
    row.appendChild(check);

    const name = document.createElement("div");
    name.className = "cstand-mlora-name";
    name.textContent = lora.name;
    name.title = lora.relative_path;
    name.addEventListener("click", () => check.click());
    row.appendChild(name);

    const strength = document.createElement("div");
    strength.className = "cstand-mlora-strength";

    const dec = document.createElement("button");
    dec.className = "cstand-mlora-step";
    dec.textContent = "-";
    strength.appendChild(dec);

    const number = document.createElement("input");
    number.className = "cstand-mlora-number";
    number.type = "number";
    number.min = "0";
    number.max = "2";
    number.step = "0.05";
    number.value = clampStrength(lora.strength).toFixed(2);
    number.addEventListener("focus", () => number.select());
    strength.appendChild(number);

    const inc = document.createElement("button");
    inc.className = "cstand-mlora-step";
    inc.textContent = "+";
    strength.appendChild(inc);

    const updateStrength = (value) => {
        const strength = clampStrength(value);
        const next = getState(node);
        next.loras = next.loras.map((item) => (
            item.relative_path === lora.relative_path
                ? { ...item, strength }
                : item
        ));
        setState(node, next);
        number.value = strength.toFixed(2);
        lora.strength = strength;
    };
    dec.addEventListener("click", () => updateStrength(clampStrength(lora.strength) - 0.05));
    inc.addEventListener("click", () => updateStrength(clampStrength(lora.strength) + 0.05));
    number.addEventListener("change", () => updateStrength(number.value));

    row.appendChild(strength);
    return row;
}
