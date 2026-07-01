import { app } from "../../scripts/app.js";

// 全セクションの情報を保持するキャッシュ
let allSourceMap = {};

async function updateMyMetadataCache() {
    try {
        const response = await fetch("/hetima_stand/model_metadata");
        allSourceMap = await response.json();
        console.log("[ComfyStand]Model metadata cache updated.");
    } catch (e) {
        console.error("[ComfyStand]Failed to update model metadata cache:", e);
    }
}


// ContextMenu用のvaluesを加工して返す
const buildMyContextMenu = function (values, options) {
    // values が配列であり、かつ中身がモデルリストであるか判定
    if (Array.isArray(values) && values.length > 0) {
        // 最初か最後の要素がモデルっぽい名前かチェック
        let checkItem = values.at(-1);
        checkItem = typeof checkItem === "string" ? checkItem : checkItem?.content;
        if (!checkItem.includes(".")) {
            checkItem = values.at(0);
            checkItem = typeof checkItem === "string" ? checkItem : checkItem?.content;
            if (!checkItem.includes(".")) {
                return values;
            }
        }

        let detectedSection = null;
        for (const section in allSourceMap) {
            if (allSourceMap[section] && allSourceMap[section][checkItem] !== undefined) {
                detectedSection = section;
                break;
            }
        }

        if (!detectedSection) {
            return values;
        }

        // モデルリストだと判明した場合、values を書き換える
        const sourceMap = allSourceMap[detectedSection];

        // ソート（文字列またはオブジェクトに対応）
        values.sort((a, b) => {
            const valA = typeof a === "string" ? a : a.content;
            const valB = typeof b === "string" ? b : b.content;
            const labelA = sourceMap[valA] || "";
            const labelB = sourceMap[valB] || "";
            if (labelA === labelB) return valA.localeCompare(valB);
            if (labelA === "") return -1;
            if (labelB === "") return 1;
            return labelA.localeCompare(labelB);
        });

        // セパレーター挿入済みの新しい配列を作成
        const newValues = [];
        let lastLabel = null;
        values.forEach(v => {
            const val = typeof v === "string" ? v : v.content;
            const currentLabel = sourceMap[val] || "";
            if (currentLabel !== lastLabel && currentLabel !== "") {
                newValues.push({
                    content: `📁 ${currentLabel}`,
                    has_submenu: false,
                    disabled: true,
                    className: "litemenu-title stand-models-menu-item-separator"
                });
            }
            newValues.push(v);
            lastLabel = currentLabel;
        });

        return newValues;
    }
    return values;
};


let targetWidget = null;
let origContextMenu = null;
const myContextMenuHook = function (values, options) {
    const newValues = buildMyContextMenu(values, options);
    if (targetWidget) {
        targetWidget.options.values = newValues;
    }
    return new origContextMenu(newValues, options);
};

const myOnClickHook = function (e, node, canvas) {
    // ウィジェットの options.values を一時的に差し替え
    // これにより、ContextMenu 内の比較 (values.length === values.length) がパスし、
    // かつ every での比較も一致するようになります

    const widget = this;
    const enabled = app.extensionManager.setting.get("Stand.EnableGroupingExtraModels", false);
    //const enabled = app.ui.settings.getSettingValue("Stand.EnableGroupingExtraModels", false);
    if (!enabled) {
        return widget.standOrigOnClick.apply(this, arguments);
    }
    const oldValues = widget.options.values;

    // 3. ContextMenu を操作するためのフック（直前差し替え）
    origContextMenu = window.LiteGraph.ContextMenu;
    window.LiteGraph.ContextMenu = myContextMenuHook;
    targetWidget = widget;
    // new 演算子で呼び出されるのでprototypeを付ける必要があるらしい
    myContextMenuHook.prototype = origContextMenu.prototype;

    try {
        // メニュー表示を実行
        return widget.standOrigOnClick.apply(this, arguments);
    } finally {
        // 元のリストに戻す
        // widget.options.values = oldValues; // too early
        // contextMenuFilter.ts 内のコンストラクタで requestAnimationFrame() が使われて、
        // その中で比較されている。
        // それが終わるまでは options.values を変更したままにしておきたい
        setTimeout(() => {
            widget.options.values = oldValues;
            targetWidget = null;
        }, 10);
        window.LiteGraph.ContextMenu = origContextMenu;
    }
};


// https://docs.comfy.org/custom-nodes/js/javascript_settings
app.registerExtension({
    name: "hetima.stand_grouping_extra_models",
    settings: [
        {
            id: "Stand.EnableGroupingExtraModels",
            name: "Enable Grouping Extra Models",
            type: "boolean",
            defaultValue: false,
            category: ["Stand", "Settings", "Setting label"],
            tooltip: "Sorts the combo box menu items by extra model path."
        }
    ],
    async setup() {


        const style = document.createElement('style');
        style.textContent = `
            .litemenu-entry.stand-models-menu-item-separator {
                color: var(--fg-color) !important;
                background-color: var(--bg-color) !important;
                opacity: 0.68 !important;
                text-align: left;
                font-weight: bold;
                pointer-events: none !important;

                /* 上下の境界線も標準カラーを薄くして利用 */
                border-top: 1px solid color-mix(in srgb, var(--fg-color) 15%, transparent) !important;
            }
        `;
        document.head.appendChild(style);

        // マッピング情報の取得
        updateMyMetadataCache();

        const origGetNodeDefs = app.api.getNodeDefs;
        app.api.getNodeDefs = async function () {
            const defs = await origGetNodeDefs.apply(this, arguments);
            await updateMyMetadataCache();
            return defs;
        };

        const origAddWidget = LGraphNode.prototype.addWidget;
        LGraphNode.prototype.addWidget = function (type, name, value, callback, options) {
            const widget = origAddWidget.apply(this, arguments);
            if (type === "combo" && widget) {
                // コンボボックスのクリック処理をフック
                const origClick = widget.onClick;
                if (!origClick) {
                    console.error("[ComfyStand] ComboWidget.onClick is null");
                    return widget;
                }
                widget.onClick = myOnClickHook;
                widget.standOrigOnClick = origClick;
            }
            return widget;
        };
    }
});
