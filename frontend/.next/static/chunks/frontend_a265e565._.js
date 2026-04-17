(globalThis.TURBOPACK || (globalThis.TURBOPACK = [])).push([typeof document === "object" ? document.currentScript : undefined,
"[project]/frontend/lib/demo-data.ts [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "demoInsights",
    ()=>demoInsights,
    "demoModelRun",
    ()=>demoModelRun,
    "demoPlayers",
    ()=>demoPlayers,
    "demoPredictions",
    ()=>demoPredictions,
    "demoTeams",
    ()=>demoTeams,
    "synthesizePrediction",
    ()=>synthesizePrediction
]);
const TEAM_SEED = [
    {
        id: "1",
        name: "Brazil",
        code: "BRA",
        confederation: "CONMEBOL"
    },
    {
        id: "2",
        name: "Argentina",
        code: "ARG",
        confederation: "CONMEBOL"
    },
    {
        id: "3",
        name: "France",
        code: "FRA",
        confederation: "UEFA"
    },
    {
        id: "4",
        name: "Germany",
        code: "GER",
        confederation: "UEFA"
    },
    {
        id: "5",
        name: "Spain",
        code: "ESP",
        confederation: "UEFA"
    },
    {
        id: "6",
        name: "England",
        code: "ENG",
        confederation: "UEFA"
    },
    {
        id: "7",
        name: "Portugal",
        code: "POR",
        confederation: "UEFA"
    },
    {
        id: "8",
        name: "Netherlands",
        code: "NED",
        confederation: "UEFA"
    },
    {
        id: "9",
        name: "Morocco",
        code: "MAR",
        confederation: "CAF"
    },
    {
        id: "10",
        name: "Japan",
        code: "JPN",
        confederation: "AFC"
    }
];
function clampProbability(value) {
    return Math.max(0.05, Math.min(0.82, value));
}
function seededHash(value) {
    return [
        ...value
    ].reduce((acc, char)=>acc * 31 + char.charCodeAt(0) >>> 0, 7);
}
function synthesizePrediction(home, away) {
    let stage = arguments.length > 2 && arguments[2] !== void 0 ? arguments[2] : "FIFA World Cup";
    const seed = Math.sin(seededHash("".concat(home, ":").concat(away, ":").concat(stage))) * 0.5;
    let pHome = clampProbability(0.45 + seed * 0.22);
    let pAway = clampProbability(0.35 - seed * 0.22);
    let pDraw = Math.max(0.08, 1 - pHome - pAway);
    const total = pHome + pAway + pDraw;
    pHome /= total;
    pAway /= total;
    pDraw /= total;
    const shap = [
        {
            feature: "elo_diff",
            value: seed * 280,
            shap: seed * 0.32
        },
        {
            feature: "top11_mean_diff",
            value: seed * 5.3,
            shap: seed * 0.21
        },
        {
            feature: "home_win_rate_10",
            value: 0.55 + seed * 0.08,
            shap: 0.08 + seed * 0.05
        },
        {
            feature: "h2h_home_wr",
            value: 0.5 + seed * 0.1,
            shap: seed * 0.06
        },
        {
            feature: "neutral",
            value: 1,
            shap: -0.02 + seed * 0.02
        }
    ];
    return {
        id: "".concat(home, "-").concat(away).toLowerCase().replace(/\s+/g, "-"),
        home,
        away,
        pHome,
        pDraw,
        pAway,
        confidence: Math.max(pHome, pDraw, pAway),
        modelVersion: "demo",
        shap
    };
}
const demoTeams = TEAM_SEED;
const demoPredictions = TEAM_SEED.flatMap((homeTeam, index)=>TEAM_SEED.slice(index + 1, index + 3).map((awayTeam)=>synthesizePrediction(homeTeam.name, awayTeam.name)));
const demoPlayers = TEAM_SEED.flatMap((team)=>Array.from({
        length: 11
    }).map((_, index)=>{
        var _team_code;
        var _team_code1, _index, _team_code_length;
        return {
            id: "".concat(team.id, "-p").concat(index + 1),
            teamId: team.id,
            teamName: team.name,
            name: "".concat((_team_code1 = team.code) !== null && _team_code1 !== void 0 ? _team_code1 : "TEAM", " Player ").concat(index + 1),
            position: (_index = [
                "GK",
                "DF",
                "DF",
                "DF",
                "DF",
                "MF",
                "MF",
                "MF",
                "FW",
                "FW",
                "FW"
            ][index]) !== null && _index !== void 0 ? _index : "MF",
            overall: 75 + (index * 3 + team.name.length) % 15,
            attrs: {
                pace: 70 + (index * 5 + team.name.length) % 24,
                shooting: 68 + (index * 4 + ((_team_code_length = (_team_code = team.code) === null || _team_code === void 0 ? void 0 : _team_code.length) !== null && _team_code_length !== void 0 ? _team_code_length : 0)) % 26,
                passing: 69 + (index * 6 + team.name.length) % 23,
                defending: 61 + (index * 7 + team.name.length) % 28
            }
        };
    }));
const demoInsights = TEAM_SEED.map((team)=>({
        entityType: "team",
        entityId: team.id,
        summaryText: "".concat(team.name, " brings strong recent-form signals, credible squad quality, and enough attacking talent to stay dangerous across knockout-state game scripts."),
        model: "demo"
    }));
const demoModelRun = {
    version: "v1",
    chosen: "stack",
    metrics: {
        lr: {
            val: {
                logLoss: 0.996,
                brier: 0.201,
                macroF1: 0.47,
                accuracy: 0.5
            },
            test: {
                logLoss: 1.004,
                brier: 0.205,
                macroF1: 0.46,
                accuracy: 0.49
            }
        },
        xgb: {
            val: {
                logLoss: 0.912,
                brier: 0.186,
                macroF1: 0.54,
                accuracy: 0.56
            },
            test: {
                logLoss: 0.924,
                brier: 0.189,
                macroF1: 0.53,
                accuracy: 0.55
            }
        },
        lgbm: {
            val: {
                logLoss: 0.918,
                brier: 0.187,
                macroF1: 0.53,
                accuracy: 0.55
            },
            test: {
                logLoss: 0.928,
                brier: 0.19,
                macroF1: 0.53,
                accuracy: 0.55
            }
        },
        nn: {
            val: {
                logLoss: 0.935,
                brier: 0.192,
                macroF1: 0.51,
                accuracy: 0.54
            },
            test: {
                logLoss: 0.947,
                brier: 0.196,
                macroF1: 0.5,
                accuracy: 0.53
            }
        },
        stack: {
            val: {
                logLoss: 0.901,
                brier: 0.183,
                macroF1: 0.55,
                accuracy: 0.57
            },
            test: {
                logLoss: 0.908,
                brier: 0.185,
                macroF1: 0.55,
                accuracy: 0.57
            }
        }
    },
    confusion: [
        [
            380,
            120,
            95
        ],
        [
            160,
            140,
            155
        ],
        [
            110,
            130,
            360
        ]
    ],
    featureImportance: [
        {
            feature: "elo_diff",
            importance: 0.22
        },
        {
            feature: "top11_mean_diff",
            importance: 0.14
        },
        {
            feature: "star3_mean_diff",
            importance: 0.09
        },
        {
            feature: "home_win_rate_10",
            importance: 0.08
        },
        {
            feature: "away_win_rate_10",
            importance: 0.07
        },
        {
            feature: "home_gd_10",
            importance: 0.06
        },
        {
            feature: "is_wc",
            importance: 0.05,
            note: "tournament flag"
        },
        {
            feature: "h2h_home_wr",
            importance: 0.045
        },
        {
            feature: "rest_home",
            importance: 0.04
        },
        {
            feature: "neutral",
            importance: 0.035
        }
    ]
};
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/frontend/components/probability-bar.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ProbabilityBar",
    ()=>ProbabilityBar
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
;
function ProbabilityBar(param) {
    let { pHome, pDraw, pAway } = param;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "probability-bar",
        "aria-label": "Prediction probabilities",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "probability-bar__segment probability-bar__segment--home",
                style: {
                    width: "".concat((pHome * 100).toFixed(1), "%")
                },
                title: "Home ".concat((pHome * 100).toFixed(1), "%")
            }, void 0, false, {
                fileName: "[project]/frontend/components/probability-bar.tsx",
                lineNumber: 10,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "probability-bar__segment probability-bar__segment--draw",
                style: {
                    width: "".concat((pDraw * 100).toFixed(1), "%")
                },
                title: "Draw ".concat((pDraw * 100).toFixed(1), "%")
            }, void 0, false, {
                fileName: "[project]/frontend/components/probability-bar.tsx",
                lineNumber: 15,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "probability-bar__segment probability-bar__segment--away",
                style: {
                    width: "".concat((pAway * 100).toFixed(1), "%")
                },
                title: "Away ".concat((pAway * 100).toFixed(1), "%")
            }, void 0, false, {
                fileName: "[project]/frontend/components/probability-bar.tsx",
                lineNumber: 20,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/frontend/components/probability-bar.tsx",
        lineNumber: 9,
        columnNumber: 5
    }, this);
}
_c = ProbabilityBar;
var _c;
__turbopack_context__.k.register(_c, "ProbabilityBar");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/frontend/components/shap-drivers.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ShapDrivers",
    ()=>ShapDrivers
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
;
function ShapDrivers(param) {
    let { drivers } = param;
    if (!drivers.length) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "empty-state",
            children: "No SHAP drivers available yet."
        }, void 0, false, {
            fileName: "[project]/frontend/components/shap-drivers.tsx",
            lineNumber: 9,
            columnNumber: 12
        }, this);
    }
    const maxAbs = Math.max(...drivers.map((driver)=>Math.abs(driver.shap)), 1);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "shap-list",
        children: drivers.map((driver)=>{
            const width = Math.abs(driver.shap) / maxAbs * 50;
            const positive = driver.shap >= 0;
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "shap-row",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "shap-row__feature",
                        children: driver.feature
                    }, void 0, false, {
                        fileName: "[project]/frontend/components/shap-drivers.tsx",
                        lineNumber: 22,
                        columnNumber: 13
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "shap-row__track",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                            className: positive ? "shap-row__bar shap-row__bar--positive" : "shap-row__bar shap-row__bar--negative",
                            style: positive ? {
                                left: "50%",
                                width: "".concat(width, "%")
                            } : {
                                right: "50%",
                                width: "".concat(width, "%")
                            }
                        }, void 0, false, {
                            fileName: "[project]/frontend/components/shap-drivers.tsx",
                            lineNumber: 24,
                            columnNumber: 15
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/frontend/components/shap-drivers.tsx",
                        lineNumber: 23,
                        columnNumber: 13
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "shap-row__value",
                        children: [
                            driver.shap >= 0 ? "+" : "",
                            driver.shap.toFixed(3)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/components/shap-drivers.tsx",
                        lineNumber: 29,
                        columnNumber: 13
                    }, this)
                ]
            }, "".concat(driver.feature, "-").concat(driver.value), true, {
                fileName: "[project]/frontend/components/shap-drivers.tsx",
                lineNumber: 21,
                columnNumber: 11
            }, this);
        })
    }, void 0, false, {
        fileName: "[project]/frontend/components/shap-drivers.tsx",
        lineNumber: 15,
        columnNumber: 5
    }, this);
}
_c = ShapDrivers;
var _c;
__turbopack_context__.k.register(_c, "ShapDrivers");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
"[project]/frontend/components/prediction-workbench.tsx [app-client] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "PredictionWorkbench",
    ()=>PredictionWorkbench
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/demo-data.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$components$2f$probability$2d$bar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/components/probability-bar.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$components$2f$shap$2d$drivers$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/components/shap-drivers.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
const defaultHome = "Brazil";
const defaultAway = "Argentina";
function pickPrediction(predictions, home, away, stage) {
    const hit = predictions.find((prediction)=>prediction.home === home && prediction.away === away || prediction.home === away && prediction.away === home);
    if (!hit) {
        return (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["synthesizePrediction"])(home, away, stage);
    }
    if (hit.home === home) {
        return hit;
    }
    return {
        ...hit,
        home,
        away,
        pHome: hit.pAway,
        pAway: hit.pHome
    };
}
function PredictionWorkbench(param) {
    let { teams, predictions } = param;
    var _teams_find, _teams_, _teams_find1, _teams_find2, _teams_1;
    _s();
    var _teams_find_name, _ref;
    const homeFallback = (_ref = (_teams_find_name = (_teams_find = teams.find((team)=>team.name === defaultHome)) === null || _teams_find === void 0 ? void 0 : _teams_find.name) !== null && _teams_find_name !== void 0 ? _teams_find_name : (_teams_ = teams[0]) === null || _teams_ === void 0 ? void 0 : _teams_.name) !== null && _ref !== void 0 ? _ref : "";
    var _teams_find_name1, _ref1, _ref2;
    const awayFallback = (_ref2 = (_ref1 = (_teams_find_name1 = (_teams_find1 = teams.find((team)=>team.name === defaultAway)) === null || _teams_find1 === void 0 ? void 0 : _teams_find1.name) !== null && _teams_find_name1 !== void 0 ? _teams_find_name1 : (_teams_find2 = teams.find((team)=>team.name !== homeFallback)) === null || _teams_find2 === void 0 ? void 0 : _teams_find2.name) !== null && _ref1 !== void 0 ? _ref1 : (_teams_1 = teams[0]) === null || _teams_1 === void 0 ? void 0 : _teams_1.name) !== null && _ref2 !== void 0 ? _ref2 : "";
    const [home, setHome] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(homeFallback);
    const [away, setAway] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(awayFallback);
    const [stage, setStage] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("FIFA World Cup");
    const [submitted, setSubmitted] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        home: homeFallback,
        away: awayFallback,
        stage: "FIFA World Cup"
    });
    const prediction = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useMemo"])({
        "PredictionWorkbench.useMemo[prediction]": ()=>pickPrediction(predictions, submitted.home, submitted.away, submitted.stage)
    }["PredictionWorkbench.useMemo[prediction]"], [
        predictions,
        submitted
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "page-stack",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "panel",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "section-heading",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "eyebrow",
                                        children: "Interactive Forecast"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 74,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                                        children: "Match prediction"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 75,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 73,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "section-copy",
                                children: "The frontend prefers live cached Supabase predictions and falls back to a deterministic local scoring preview when a requested fixture is not already available."
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 77,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                        lineNumber: 72,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "control-grid",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                className: "field",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        children: "Home team"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 85,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                        value: home,
                                        onChange: (event)=>setHome(event.target.value),
                                        children: teams.map((team)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                value: team.name,
                                                children: team.name
                                            }, team.id, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 88,
                                                columnNumber: 17
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 86,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 84,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                className: "field",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        children: "Away team"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 96,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                        value: away,
                                        onChange: (event)=>setAway(event.target.value),
                                        children: teams.map((team)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                value: team.name,
                                                children: team.name
                                            }, team.id, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 99,
                                                columnNumber: 17
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 97,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 95,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                className: "field",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        children: "Stage"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 107,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                        value: stage,
                                        onChange: (event)=>setStage(event.target.value),
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                children: "FIFA World Cup"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 109,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                children: "FIFA World Cup qualification"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 110,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                children: "Friendly"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 111,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                children: "UEFA Euro"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 112,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 108,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 106,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                className: "primary-button",
                                type: "button",
                                onClick: ()=>setSubmitted({
                                        home,
                                        away,
                                        stage
                                    }),
                                disabled: !home || !away || home === away,
                                children: "Predict"
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 116,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                        lineNumber: 83,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                lineNumber: 71,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "two-column-grid",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "eyebrow",
                                children: "Scored Fixture"
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 129,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                className: "matchup-title",
                                children: [
                                    prediction.home,
                                    " vs ",
                                    prediction.away
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 130,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "triplet",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        children: [
                                            "Home ",
                                            (prediction.pHome * 100).toFixed(1),
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 134,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        children: [
                                            "Draw ",
                                            (prediction.pDraw * 100).toFixed(1),
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 135,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                        children: [
                                            "Away ",
                                            (prediction.pAway * 100).toFixed(1),
                                            "%"
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 136,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 133,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$components$2f$probability$2d$bar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ProbabilityBar"], {
                                pHome: prediction.pHome,
                                pDraw: prediction.pDraw,
                                pAway: prediction.pAway
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 138,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "detail-list",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Confidence"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 141,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: [
                                                    (prediction.confidence * 100).toFixed(1),
                                                    "%"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 142,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 140,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Model version"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 145,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: prediction.modelVersion
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 146,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 144,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Stage context"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 149,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: submitted.stage
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                                lineNumber: 150,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                        lineNumber: 148,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 139,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                        lineNumber: 128,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "eyebrow",
                                children: "Explainability"
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 156,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                children: "Why this prediction?"
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 157,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "section-copy",
                                children: "Positive SHAP values push the forecast toward the home side. Negative values weaken the home-win case."
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 158,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$components$2f$shap$2d$drivers$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["ShapDrivers"], {
                                drivers: prediction.shap
                            }, void 0, false, {
                                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                                lineNumber: 161,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/components/prediction-workbench.tsx",
                        lineNumber: 155,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/frontend/components/prediction-workbench.tsx",
                lineNumber: 127,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/frontend/components/prediction-workbench.tsx",
        lineNumber: 70,
        columnNumber: 5
    }, this);
}
_s(PredictionWorkbench, "xnCyQQEZ+CQ4txqITwG+0OMmi9A=");
_c = PredictionWorkbench;
var _c;
__turbopack_context__.k.register(_c, "PredictionWorkbench");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(__turbopack_context__.m, globalThis.$RefreshHelpers$);
}
}),
]);

//# sourceMappingURL=frontend_a265e565._.js.map