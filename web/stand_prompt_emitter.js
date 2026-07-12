import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const NODE_NAME = "StandPromptEmitter";
const TEXT_WIDGET_TYPES = new Set(["string", "text", "customtext"]);

function getTargetNodeId(node) {
    const widget = node.widgets?.find((item) => item.name === "target_node_id");
    const value = Number(widget?.value ?? 0);
    return Number.isFinite(value) ? Math.trunc(value) : 0;
}

function findTextWidget(node) {
    const widgets = node?.widgets || [];
    const preferred = widgets.find((widget) => {
        const name = String(widget.name || "").toLowerCase();
        return name === "text" || name === "prompt" || name === "positive" || name === "negative";
    });
    if (preferred) return preferred;

    return widgets.find((widget) => {
        const type = String(widget.type || "").toLowerCase().split(":")[0];
        return TEXT_WIDGET_TYPES.has(type);
    });
}

function setTextWidget(nodeId, text) {
    const node = app.graph.getNodeById(Number(nodeId));
    const widget = findTextWidget(node);
    if (!node || !widget) {
        console.warn("[ComfyStand] Stand Prompt Emitter target text widget not found:", nodeId);
        return false;
    }

    widget.value = text;
    widget.callback?.(text, app.canvas, node, null, widget);
    node.setDirtyCanvas?.(true, true);
    app.graph.setDirtyCanvas(true, true);
    return true;
}

function collectPromptNode(nodeId, source, target) {
    const key = String(nodeId);
    if (target[key] || !source[key]) return;

    target[key] = source[key];
    for (const input of Object.values(source[key].inputs || {})) {
        if (Array.isArray(input)) {
            collectPromptNode(input[0], source, target);
        }
    }
}

function setNodeMode(node, mode) {
    node.mode = mode;
    node.setDirtyCanvas?.(true, true);
    app.graph.setDirtyCanvas(true, true);
}

function ensurePromptEmitterUi(node) {
    node.serialize_widgets = true;
    if (node.comfystandPromptEmitterButton) return;

    node.comfystandPromptEmitterButton = node.addWidget("button", "Apply", null, async () => {
        const targetNodeId = getTargetNodeId(node);
        if (!targetNodeId) {
            console.warn("[ComfyStand] Stand Prompt Emitter target_node_id is empty.");
            return;
        }

        try {
            await queueEmitterNode(node);
        } catch (error) {
            console.error("[ComfyStand] Stand Prompt Emitter apply failed:", error);
        }
    });
    node.comfystandPromptEmitterButton.serialize = false;
}

async function queueEmitterNode(node) {
    const oldMode = node.mode;
    const alwaysMode = window.LiteGraph?.ALWAYS ?? 0;

    try {
        setNodeMode(node, alwaysMode);
        const prompt = await app.graphToPrompt();
        const output = {};
        collectPromptNode(node.id, prompt.output, output);
        prompt.output = output;
        await api.queuePrompt(0, prompt);
    } finally {
        setNodeMode(node, oldMode);
    }
}

api.addEventListener("comfystand.prompt_emitted", (event) => {
    const { target_node_id, text } = event.detail || {};
    if (!target_node_id) {
        console.warn("[ComfyStand] Stand Prompt Emitter target_node_id is empty.");
        return;
    }
    setTextWidget(target_node_id, text || "");
});

app.registerExtension({
    name: "hetima.stand_prompt_emitter",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            originalOnNodeCreated?.apply(this, arguments);
            ensurePromptEmitterUi(this);
        };

        const originalConfigure = nodeType.prototype.configure;
        nodeType.prototype.configure = function () {
            originalConfigure?.apply(this, arguments);
            ensurePromptEmitterUi(this);
        };
    },
});
