module.exports = [
"[project]/frontend/.next-internal/server/app/page/actions.js [app-rsc] (server actions loader, ecmascript)", ((__turbopack_context__, module, exports) => {

}),
"[project]/frontend/app/layout.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/frontend/app/layout.tsx [app-rsc] (ecmascript)"));
}),
"[project]/frontend/components/probability-bar.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "ProbabilityBar",
    ()=>ProbabilityBar
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
;
function ProbabilityBar({ pHome, pDraw, pAway }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "probability-bar",
        "aria-label": "Prediction probabilities",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "probability-bar__segment probability-bar__segment--home",
                style: {
                    width: `${(pHome * 100).toFixed(1)}%`
                },
                title: `Home ${(pHome * 100).toFixed(1)}%`
            }, void 0, false, {
                fileName: "[project]/frontend/components/probability-bar.tsx",
                lineNumber: 10,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "probability-bar__segment probability-bar__segment--draw",
                style: {
                    width: `${(pDraw * 100).toFixed(1)}%`
                },
                title: `Draw ${(pDraw * 100).toFixed(1)}%`
            }, void 0, false, {
                fileName: "[project]/frontend/components/probability-bar.tsx",
                lineNumber: 15,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "probability-bar__segment probability-bar__segment--away",
                style: {
                    width: `${(pAway * 100).toFixed(1)}%`
                },
                title: `Away ${(pAway * 100).toFixed(1)}%`
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
}),
"[project]/frontend/lib/demo-data.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
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
function synthesizePrediction(home, away, stage = "FIFA World Cup") {
    const seed = Math.sin(seededHash(`${home}:${away}:${stage}`)) * 0.5;
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
        id: `${home}-${away}`.toLowerCase().replace(/\s+/g, "-"),
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
const DEMO_SQUADS = {
    Brazil: [
        {
            name: "Alisson",
            position: "GK",
            clubName: "Liverpool",
            foot: "Right",
            base: 87
        },
        {
            name: "Danilo",
            position: "DF",
            clubName: "Juventus",
            foot: "Right",
            base: 80
        },
        {
            name: "Marquinhos",
            position: "DF",
            clubName: "Paris Saint-Germain",
            foot: "Right",
            base: 87
        },
        {
            name: "Gabriel Magalhaes",
            position: "DF",
            clubName: "Arsenal",
            foot: "Left",
            base: 83
        },
        {
            name: "Guilherme Arana",
            position: "DF",
            clubName: "Atletico Mineiro",
            foot: "Left",
            base: 79
        },
        {
            name: "Bruno Guimaraes",
            position: "MF",
            clubName: "Newcastle United",
            foot: "Right",
            base: 85
        },
        {
            name: "Joao Gomes",
            position: "MF",
            clubName: "Wolverhampton Wanderers",
            foot: "Right",
            base: 79
        },
        {
            name: "Lucas Paqueta",
            position: "MF",
            clubName: "West Ham United",
            foot: "Left",
            base: 83
        },
        {
            name: "Rodrygo",
            position: "FW",
            clubName: "Real Madrid",
            foot: "Right",
            base: 86
        },
        {
            name: "Vinicius Junior",
            position: "FW",
            clubName: "Real Madrid",
            foot: "Right",
            base: 89
        },
        {
            name: "Raphinha",
            position: "FW",
            clubName: "Barcelona",
            foot: "Left",
            base: 84
        }
    ],
    Argentina: [
        {
            name: "Emiliano Martinez",
            position: "GK",
            clubName: "Aston Villa",
            foot: "Right",
            base: 86
        },
        {
            name: "Nahuel Molina",
            position: "DF",
            clubName: "Atletico Madrid",
            foot: "Right",
            base: 82
        },
        {
            name: "Cristian Romero",
            position: "DF",
            clubName: "Tottenham Hotspur",
            foot: "Right",
            base: 86
        },
        {
            name: "Lisandro Martinez",
            position: "DF",
            clubName: "Manchester United",
            foot: "Left",
            base: 84
        },
        {
            name: "Nicolas Tagliafico",
            position: "DF",
            clubName: "Lyon",
            foot: "Left",
            base: 80
        },
        {
            name: "Enzo Fernandez",
            position: "MF",
            clubName: "Chelsea",
            foot: "Right",
            base: 85
        },
        {
            name: "Alexis Mac Allister",
            position: "MF",
            clubName: "Liverpool",
            foot: "Right",
            base: 85
        },
        {
            name: "Rodrigo De Paul",
            position: "MF",
            clubName: "Atletico Madrid",
            foot: "Right",
            base: 84
        },
        {
            name: "Lionel Messi",
            position: "FW",
            clubName: "Inter Miami",
            foot: "Left",
            base: 90
        },
        {
            name: "Julian Alvarez",
            position: "FW",
            clubName: "Manchester City",
            foot: "Right",
            base: 86
        },
        {
            name: "Lautaro Martinez",
            position: "FW",
            clubName: "Inter",
            foot: "Right",
            base: 88
        }
    ],
    France: [
        {
            name: "Mike Maignan",
            position: "GK",
            clubName: "AC Milan",
            foot: "Right",
            base: 87
        },
        {
            name: "Jules Kounde",
            position: "DF",
            clubName: "Barcelona",
            foot: "Right",
            base: 85
        },
        {
            name: "William Saliba",
            position: "DF",
            clubName: "Arsenal",
            foot: "Right",
            base: 86
        },
        {
            name: "Dayot Upamecano",
            position: "DF",
            clubName: "Bayern Munich",
            foot: "Right",
            base: 84
        },
        {
            name: "Theo Hernandez",
            position: "DF",
            clubName: "AC Milan",
            foot: "Left",
            base: 86
        },
        {
            name: "Aurelien Tchouameni",
            position: "MF",
            clubName: "Real Madrid",
            foot: "Right",
            base: 86
        },
        {
            name: "Eduardo Camavinga",
            position: "MF",
            clubName: "Real Madrid",
            foot: "Left",
            base: 85
        },
        {
            name: "Antoine Griezmann",
            position: "FW",
            clubName: "Atletico Madrid",
            foot: "Left",
            base: 87
        },
        {
            name: "Ousmane Dembele",
            position: "FW",
            clubName: "Paris Saint-Germain",
            foot: "Both",
            base: 86
        },
        {
            name: "Kylian Mbappe",
            position: "FW",
            clubName: "Real Madrid",
            foot: "Right",
            base: 92
        },
        {
            name: "Marcus Thuram",
            position: "FW",
            clubName: "Inter",
            foot: "Right",
            base: 84
        }
    ],
    Germany: [
        {
            name: "Marc-Andre ter Stegen",
            position: "GK",
            clubName: "Barcelona",
            foot: "Right",
            base: 89
        },
        {
            name: "Joshua Kimmich",
            position: "DF",
            clubName: "Bayern Munich",
            foot: "Right",
            base: 86
        },
        {
            name: "Antonio Rudiger",
            position: "DF",
            clubName: "Real Madrid",
            foot: "Right",
            base: 86
        },
        {
            name: "Jonathan Tah",
            position: "DF",
            clubName: "Bayer Leverkusen",
            foot: "Right",
            base: 83
        },
        {
            name: "David Raum",
            position: "DF",
            clubName: "RB Leipzig",
            foot: "Left",
            base: 82
        },
        {
            name: "Jamal Musiala",
            position: "MF",
            clubName: "Bayern Munich",
            foot: "Right",
            base: 88
        },
        {
            name: "Ilkay Gundogan",
            position: "MF",
            clubName: "Barcelona",
            foot: "Right",
            base: 85
        },
        {
            name: "Florian Wirtz",
            position: "MF",
            clubName: "Bayer Leverkusen",
            foot: "Right",
            base: 88
        },
        {
            name: "Leroy Sane",
            position: "FW",
            clubName: "Bayern Munich",
            foot: "Left",
            base: 84
        },
        {
            name: "Kai Havertz",
            position: "FW",
            clubName: "Arsenal",
            foot: "Left",
            base: 83
        },
        {
            name: "Niclas Fullkrug",
            position: "FW",
            clubName: "Borussia Dortmund",
            foot: "Right",
            base: 81
        }
    ],
    Spain: [
        {
            name: "Unai Simon",
            position: "GK",
            clubName: "Athletic Club",
            foot: "Right",
            base: 84
        },
        {
            name: "Dani Carvajal",
            position: "DF",
            clubName: "Real Madrid",
            foot: "Right",
            base: 85
        },
        {
            name: "Aymeric Laporte",
            position: "DF",
            clubName: "Al Nassr",
            foot: "Left",
            base: 84
        },
        {
            name: "Robin Le Normand",
            position: "DF",
            clubName: "Atletico Madrid",
            foot: "Right",
            base: 83
        },
        {
            name: "Alejandro Grimaldo",
            position: "DF",
            clubName: "Bayer Leverkusen",
            foot: "Left",
            base: 84
        },
        {
            name: "Rodri",
            position: "MF",
            clubName: "Manchester City",
            foot: "Right",
            base: 91
        },
        {
            name: "Pedri",
            position: "MF",
            clubName: "Barcelona",
            foot: "Right",
            base: 87
        },
        {
            name: "Fabian Ruiz",
            position: "MF",
            clubName: "Paris Saint-Germain",
            foot: "Left",
            base: 83
        },
        {
            name: "Lamine Yamal",
            position: "FW",
            clubName: "Barcelona",
            foot: "Left",
            base: 84
        },
        {
            name: "Nico Williams",
            position: "FW",
            clubName: "Athletic Club",
            foot: "Right",
            base: 84
        },
        {
            name: "Alvaro Morata",
            position: "FW",
            clubName: "AC Milan",
            foot: "Right",
            base: 82
        }
    ],
    England: [
        {
            name: "Jordan Pickford",
            position: "GK",
            clubName: "Everton",
            foot: "Left",
            base: 83
        },
        {
            name: "Kyle Walker",
            position: "DF",
            clubName: "Manchester City",
            foot: "Right",
            base: 83
        },
        {
            name: "John Stones",
            position: "DF",
            clubName: "Manchester City",
            foot: "Right",
            base: 85
        },
        {
            name: "Marc Guehi",
            position: "DF",
            clubName: "Crystal Palace",
            foot: "Right",
            base: 81
        },
        {
            name: "Luke Shaw",
            position: "DF",
            clubName: "Manchester United",
            foot: "Left",
            base: 82
        },
        {
            name: "Declan Rice",
            position: "MF",
            clubName: "Arsenal",
            foot: "Right",
            base: 87
        },
        {
            name: "Jude Bellingham",
            position: "MF",
            clubName: "Real Madrid",
            foot: "Right",
            base: 90
        },
        {
            name: "Phil Foden",
            position: "FW",
            clubName: "Manchester City",
            foot: "Left",
            base: 88
        },
        {
            name: "Bukayo Saka",
            position: "FW",
            clubName: "Arsenal",
            foot: "Left",
            base: 88
        },
        {
            name: "Harry Kane",
            position: "FW",
            clubName: "Bayern Munich",
            foot: "Right",
            base: 90
        },
        {
            name: "Cole Palmer",
            position: "FW",
            clubName: "Chelsea",
            foot: "Left",
            base: 86
        }
    ],
    Portugal: [
        {
            name: "Diogo Costa",
            position: "GK",
            clubName: "Porto",
            foot: "Right",
            base: 85
        },
        {
            name: "Joao Cancelo",
            position: "DF",
            clubName: "Al Hilal",
            foot: "Right",
            base: 84
        },
        {
            name: "Ruben Dias",
            position: "DF",
            clubName: "Manchester City",
            foot: "Right",
            base: 88
        },
        {
            name: "Goncalo Inacio",
            position: "DF",
            clubName: "Sporting CP",
            foot: "Left",
            base: 82
        },
        {
            name: "Nuno Mendes",
            position: "DF",
            clubName: "Paris Saint-Germain",
            foot: "Left",
            base: 84
        },
        {
            name: "Bruno Fernandes",
            position: "MF",
            clubName: "Manchester United",
            foot: "Right",
            base: 88
        },
        {
            name: "Vitinha",
            position: "MF",
            clubName: "Paris Saint-Germain",
            foot: "Right",
            base: 85
        },
        {
            name: "Bernardo Silva",
            position: "MF",
            clubName: "Manchester City",
            foot: "Left",
            base: 88
        },
        {
            name: "Rafael Leao",
            position: "FW",
            clubName: "AC Milan",
            foot: "Right",
            base: 86
        },
        {
            name: "Cristiano Ronaldo",
            position: "FW",
            clubName: "Al Nassr",
            foot: "Right",
            base: 86
        },
        {
            name: "Joao Felix",
            position: "FW",
            clubName: "Chelsea",
            foot: "Right",
            base: 82
        }
    ],
    Netherlands: [
        {
            name: "Bart Verbruggen",
            position: "GK",
            clubName: "Brighton",
            foot: "Right",
            base: 80
        },
        {
            name: "Denzel Dumfries",
            position: "DF",
            clubName: "Inter",
            foot: "Right",
            base: 83
        },
        {
            name: "Virgil van Dijk",
            position: "DF",
            clubName: "Liverpool",
            foot: "Right",
            base: 89
        },
        {
            name: "Matthijs de Ligt",
            position: "DF",
            clubName: "Manchester United",
            foot: "Right",
            base: 84
        },
        {
            name: "Nathan Ake",
            position: "DF",
            clubName: "Manchester City",
            foot: "Left",
            base: 84
        },
        {
            name: "Frenkie de Jong",
            position: "MF",
            clubName: "Barcelona",
            foot: "Right",
            base: 87
        },
        {
            name: "Tijjani Reijnders",
            position: "MF",
            clubName: "AC Milan",
            foot: "Right",
            base: 83
        },
        {
            name: "Xavi Simons",
            position: "MF",
            clubName: "RB Leipzig",
            foot: "Right",
            base: 84
        },
        {
            name: "Cody Gakpo",
            position: "FW",
            clubName: "Liverpool",
            foot: "Right",
            base: 84
        },
        {
            name: "Memphis Depay",
            position: "FW",
            clubName: "Corinthians",
            foot: "Right",
            base: 82
        },
        {
            name: "Donyell Malen",
            position: "FW",
            clubName: "Borussia Dortmund",
            foot: "Right",
            base: 82
        }
    ],
    Morocco: [
        {
            name: "Yassine Bounou",
            position: "GK",
            clubName: "Al Hilal",
            foot: "Left",
            base: 84
        },
        {
            name: "Achraf Hakimi",
            position: "DF",
            clubName: "Paris Saint-Germain",
            foot: "Right",
            base: 86
        },
        {
            name: "Nayef Aguerd",
            position: "DF",
            clubName: "West Ham United",
            foot: "Left",
            base: 81
        },
        {
            name: "Romain Saiss",
            position: "DF",
            clubName: "Al Sadd",
            foot: "Left",
            base: 79
        },
        {
            name: "Noussair Mazraoui",
            position: "DF",
            clubName: "Manchester United",
            foot: "Right",
            base: 82
        },
        {
            name: "Sofyan Amrabat",
            position: "MF",
            clubName: "Fenerbahce",
            foot: "Right",
            base: 82
        },
        {
            name: "Azzedine Ounahi",
            position: "MF",
            clubName: "Marseille",
            foot: "Right",
            base: 79
        },
        {
            name: "Bilal El Khannouss",
            position: "MF",
            clubName: "Genk",
            foot: "Right",
            base: 77
        },
        {
            name: "Hakim Ziyech",
            position: "FW",
            clubName: "Al Duhail",
            foot: "Left",
            base: 81
        },
        {
            name: "Youssef En-Nesyri",
            position: "FW",
            clubName: "Fenerbahce",
            foot: "Left",
            base: 82
        },
        {
            name: "Brahim Diaz",
            position: "FW",
            clubName: "Real Madrid",
            foot: "Left",
            base: 83
        }
    ],
    Japan: [
        {
            name: "Zion Suzuki",
            position: "GK",
            clubName: "Parma",
            foot: "Right",
            base: 77
        },
        {
            name: "Takehiro Tomiyasu",
            position: "DF",
            clubName: "Arsenal",
            foot: "Right",
            base: 82
        },
        {
            name: "Ko Itakura",
            position: "DF",
            clubName: "Borussia Monchengladbach",
            foot: "Right",
            base: 79
        },
        {
            name: "Shogo Taniguchi",
            position: "DF",
            clubName: "Sint-Truiden",
            foot: "Right",
            base: 76
        },
        {
            name: "Hiroki Ito",
            position: "DF",
            clubName: "Bayern Munich",
            foot: "Left",
            base: 79
        },
        {
            name: "Wataru Endo",
            position: "MF",
            clubName: "Liverpool",
            foot: "Right",
            base: 81
        },
        {
            name: "Hidemasa Morita",
            position: "MF",
            clubName: "Sporting CP",
            foot: "Right",
            base: 79
        },
        {
            name: "Daichi Kamada",
            position: "MF",
            clubName: "Crystal Palace",
            foot: "Right",
            base: 80
        },
        {
            name: "Kaoru Mitoma",
            position: "FW",
            clubName: "Brighton",
            foot: "Right",
            base: 83
        },
        {
            name: "Takefusa Kubo",
            position: "FW",
            clubName: "Real Sociedad",
            foot: "Left",
            base: 84
        },
        {
            name: "Ayase Ueda",
            position: "FW",
            clubName: "Feyenoord",
            foot: "Right",
            base: 78
        }
    ]
};
function demoPlayerProfile(team, index, base) {
    const attributeBump = team.name.length % 5;
    const age = 23 + (index + team.id.length) % 9;
    return {
        id: `${team.id}-p${index + 1}`,
        teamId: team.id,
        teamName: team.name,
        name: base.name,
        position: base.position,
        overall: base.base,
        clubName: base.clubName,
        age,
        potential: Math.min(94, base.base + 3),
        preferredFoot: base.foot,
        valueEur: (base.base - 68) * 3_500_000,
        wageEur: (base.base - 60) * 4_000,
        attrs: {
            pace: Math.min(95, base.base + (base.position === "FW" ? 5 : 1)),
            shooting: Math.min(94, base.base + (base.position === "FW" ? 4 : -2)),
            passing: Math.min(93, base.base + (base.position === "MF" ? 4 : 0)),
            defending: Math.max(38, base.base + (base.position === "DF" ? 5 : -8)),
            dribbling: Math.min(94, base.base + (base.position === "FW" || base.position === "MF" ? 4 : -1)),
            physic: Math.min(92, base.base + (base.position === "DF" ? 3 : 1)),
            heightCm: 176 + (index * 2 + attributeBump) % 17,
            weightKg: 70 + (index * 3 + attributeBump) % 14,
            internationalReputation: Math.min(5, Math.max(1, Math.round((base.base - 74) / 4)))
        },
        insightSummary: `${base.name} anchors ${team.name}'s lineup from ${base.clubName}, with a ${base.foot.toLowerCase()}-foot profile and a strong overall rating of ${base.base}.`
    };
}
const demoPlayers = TEAM_SEED.flatMap((team)=>{
    const squad = DEMO_SQUADS[team.name];
    if (!squad) {
        return [];
    }
    return squad.map((player, index)=>demoPlayerProfile(team, index, player));
});
const demoInsights = TEAM_SEED.map((team)=>({
        entityType: "team",
        entityId: team.id,
        summaryText: `${team.name} brings strong recent-form signals, credible squad quality, and enough attacking talent to stay dangerous across knockout-state game scripts.`,
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
}),
"[project]/frontend/lib/supabase.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "getSupabaseClient",
    ()=>getSupabaseClient
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$server$2d$only$2f$empty$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/server-only/empty.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f40$supabase$2f$supabase$2d$js$2f$dist$2f$index$2e$mjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$locals$3e$__ = __turbopack_context__.i("[project]/frontend/node_modules/@supabase/supabase-js/dist/index.mjs [app-rsc] (ecmascript) <locals>");
;
;
let supabaseClient;
function getSupabaseClient() {
    if (supabaseClient !== undefined) {
        return supabaseClient;
    }
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
    if (!url || !anonKey) {
        supabaseClient = null;
        return supabaseClient;
    }
    supabaseClient = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f40$supabase$2f$supabase$2d$js$2f$dist$2f$index$2e$mjs__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__$3c$locals$3e$__["createClient"])(url, anonKey, {
        auth: {
            autoRefreshToken: false,
            persistSession: false
        }
    });
    return supabaseClient;
}
}),
"[project]/frontend/lib/data.ts [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "latestModelRun",
    ()=>latestModelRun,
    "listInsights",
    ()=>listInsights,
    "listPlayers",
    ()=>listPlayers,
    "listPredictions",
    ()=>listPredictions,
    "listTeams",
    ()=>listTeams
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$compiled$2f$server$2d$only$2f$empty$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/compiled/server-only/empty.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/demo-data.ts [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$supabase$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/supabase.ts [app-rsc] (ecmascript)");
;
;
;
;
function isRecord(value) {
    return typeof value === "object" && value !== null;
}
function readString(value, fallback = "") {
    return typeof value === "string" ? value : fallback;
}
function readNullableString(value) {
    return typeof value === "string" ? value : null;
}
function readNumber(value, fallback = 0) {
    if (typeof value === "number" && Number.isFinite(value)) {
        return value;
    }
    if (typeof value === "string") {
        const parsed = Number(value);
        if (Number.isFinite(parsed)) {
            return parsed;
        }
    }
    return fallback;
}
function normalizeTeam(row) {
    if (!isRecord(row)) {
        return null;
    }
    const id = readString(row.id);
    const name = readString(row.name);
    if (!id || !name) {
        return null;
    }
    return {
        id,
        name,
        code: readNullableString(row.code),
        confederation: readNullableString(row.confederation)
    };
}
function normalizeShap(value) {
    if (!Array.isArray(value)) {
        return [];
    }
    return value.map((item)=>{
        if (!isRecord(item)) {
            return null;
        }
        return {
            feature: readString(item.feature, "unknown_feature"),
            value: readNumber(item.value),
            shap: readNumber(item.shap)
        };
    }).filter((item)=>item !== null);
}
function normalizePlayerAttributes(value) {
    if (!isRecord(value)) {
        return {
            pace: 0,
            shooting: 0,
            passing: 0,
            defending: 0,
            dribbling: 0,
            physic: 0,
            heightCm: 0,
            weightKg: 0,
            internationalReputation: 0
        };
    }
    return {
        pace: readNumber(value.pace),
        shooting: readNumber(value.shooting),
        passing: readNumber(value.passing),
        defending: readNumber(value.defending),
        dribbling: readNumber(value.dribbling),
        physic: readNumber(value.physic),
        heightCm: readNumber(value.height_cm ?? value.heightCm),
        weightKg: readNumber(value.weight_kg ?? value.weightKg),
        internationalReputation: readNumber(value.international_reputation ?? value.internationalReputation)
    };
}
function normalizeMetricSnapshot(value) {
    if (!isRecord(value)) {
        return {
            logLoss: 0,
            brier: 0,
            macroF1: 0,
            accuracy: 0
        };
    }
    return {
        logLoss: readNumber(value.log_loss ?? value.logLoss),
        brier: readNumber(value.brier),
        macroF1: readNumber(value.macro_f1 ?? value.macroF1),
        accuracy: readNumber(value.accuracy)
    };
}
function normalizeModelMetric(value) {
    if (!isRecord(value)) {
        return {
            val: {
                logLoss: 0,
                brier: 0,
                macroF1: 0,
                accuracy: 0
            },
            test: {
                logLoss: 0,
                brier: 0,
                macroF1: 0,
                accuracy: 0
            }
        };
    }
    return {
        val: normalizeMetricSnapshot(value.val),
        test: normalizeMetricSnapshot(value.test)
    };
}
function normalizeModelKey(value) {
    const key = readString(value);
    return key === "lr" || key === "xgb" || key === "lgbm" || key === "nn" || key === "stack" ? key : __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"].chosen;
}
function normalizeMetrics(value) {
    if (!isRecord(value)) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"].metrics;
    }
    return {
        lr: normalizeModelMetric(value.lr),
        xgb: normalizeModelMetric(value.xgb),
        lgbm: normalizeModelMetric(value.lgbm),
        nn: normalizeModelMetric(value.nn),
        stack: normalizeModelMetric(value.stack)
    };
}
const listTeams = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["cache"])(async ()=>{
    const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$supabase$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
    if (!supabase) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoTeams"];
    }
    const result = await supabase.from("teams").select("id, name, code, confederation").order("name");
    const data = Array.isArray(result.data) ? result.data.map(normalizeTeam).filter((team)=>team !== null) : [];
    return data.length ? data : __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoTeams"];
});
const listPredictions = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["cache"])(async ()=>{
    const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$supabase$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
    if (!supabase) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoPredictions"];
    }
    const predictionResult = await supabase.from("predictions").select("id, match_id, p_home, p_draw, p_away, confidence, model_version, shap").order("created_at", {
        ascending: false
    }).limit(40);
    if (!Array.isArray(predictionResult.data) || !predictionResult.data.length) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoPredictions"];
    }
    const rows = predictionResult.data.filter(isRecord);
    const matchIds = rows.map((row)=>readString(row.match_id)).filter(Boolean);
    const matchResult = await supabase.from("matches").select("id, home_id, away_id").in("id", matchIds);
    const matchRows = Array.isArray(matchResult.data) ? matchResult.data.filter(isRecord) : [];
    const teamIds = matchRows.flatMap((row)=>[
            readString(row.home_id),
            readString(row.away_id)
        ]).filter(Boolean);
    const uniqueTeamIds = [
        ...new Set(teamIds)
    ];
    const teamResult = await supabase.from("teams").select("id, name").in("id", uniqueTeamIds);
    const teamRows = Array.isArray(teamResult.data) ? teamResult.data.filter(isRecord) : [];
    const teamById = new Map(teamRows.map((row)=>[
            readString(row.id),
            readString(row.name)
        ]).filter(([id, name])=>id && name));
    const matchesById = new Map(matchRows.map((row)=>[
            readString(row.id),
            {
                homeId: readString(row.home_id),
                awayId: readString(row.away_id)
            }
        ]).filter(([id, match])=>id && match.homeId && match.awayId));
    const predictions = rows.map((row)=>{
        const matchId = readString(row.match_id);
        const match = matchesById.get(matchId);
        const home = match ? teamById.get(match.homeId) : null;
        const away = match ? teamById.get(match.awayId) : null;
        if (!match || !home || !away) {
            return null;
        }
        return {
            id: readString(row.id, `${home}-${away}`),
            home,
            away,
            pHome: readNumber(row.p_home),
            pDraw: readNumber(row.p_draw),
            pAway: readNumber(row.p_away),
            confidence: readNumber(row.confidence),
            modelVersion: readString(row.model_version, "v1"),
            shap: normalizeShap(row.shap)
        };
    }).filter((prediction)=>prediction !== null);
    return predictions.length ? predictions : __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoPredictions"];
});
const listPlayers = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["cache"])(async ()=>{
    const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$supabase$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
    if (!supabase) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoPlayers"];
    }
    const playerInsights = await listInsights("player");
    const insightById = new Map(playerInsights.map((insight)=>[
            insight.entityId,
            insight.summaryText
        ]));
    const playerResult = await supabase.from("players").select("id, team_id, name, position, overall, club_name, age, potential, preferred_foot, value_eur, wage_eur, attrs").order("overall", {
        ascending: false
    }).limit(300);
    if (!Array.isArray(playerResult.data) || !playerResult.data.length) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoPlayers"];
    }
    const teams = await listTeams();
    const teamById = new Map(teams.map((team)=>[
            team.id,
            team.name
        ]));
    const players = [];
    for (const row of playerResult.data.filter(isRecord)){
        const teamId = readString(row.team_id);
        const teamName = teamById.get(teamId);
        const id = readString(row.id);
        const name = readString(row.name);
        if (!id || !name || !teamId || !teamName) {
            continue;
        }
        players.push({
            id,
            teamId,
            teamName,
            name,
            position: readString(row.position, "MF"),
            overall: readNumber(row.overall),
            clubName: readNullableString(row.club_name),
            age: row.age === null || row.age === undefined ? null : readNumber(row.age),
            potential: row.potential === null || row.potential === undefined ? null : readNumber(row.potential),
            preferredFoot: readNullableString(row.preferred_foot),
            valueEur: row.value_eur === null || row.value_eur === undefined ? null : readNumber(row.value_eur),
            wageEur: row.wage_eur === null || row.wage_eur === undefined ? null : readNumber(row.wage_eur),
            attrs: normalizePlayerAttributes(row.attrs),
            insightSummary: insightById.get(id)
        });
    }
    return players.length ? players : __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoPlayers"];
});
const listInsights = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["cache"])(async (entityType)=>{
    const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$supabase$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
    if (!supabase) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoInsights"].filter((insight)=>insight.entityType === entityType);
    }
    const result = await supabase.from("insights").select("entity_type, entity_id, summary_text, model").eq("entity_type", entityType);
    if (!Array.isArray(result.data) || !result.data.length) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoInsights"].filter((insight)=>insight.entityType === entityType);
    }
    const insights = result.data.filter(isRecord).map((row)=>{
        const entityId = readString(row.entity_id);
        const summaryText = readString(row.summary_text);
        if (!entityId || !summaryText) {
            return null;
        }
        return {
            entityType,
            entityId,
            summaryText,
            model: readNullableString(row.model)
        };
    }).filter((insight)=>insight !== null);
    return insights.length ? insights : __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoInsights"].filter((insight)=>insight.entityType === entityType);
});
const latestModelRun = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["cache"])(async ()=>{
    const supabase = (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$supabase$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["getSupabaseClient"])();
    if (!supabase) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"];
    }
    const result = await supabase.from("model_runs").select("version, algo, metrics").order("created_at", {
        ascending: false
    }).limit(1);
    const row = Array.isArray(result.data) ? result.data.find(isRecord) : null;
    if (!row) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"];
    }
    return {
        version: readString(row.version, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"].version),
        chosen: normalizeModelKey(row.algo),
        metrics: normalizeMetrics(row.metrics),
        confusion: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"].confusion,
        featureImportance: __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$demo$2d$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["demoModelRun"].featureImportance
    };
});
}),
"[project]/frontend/app/page.tsx [app-rsc] (ecmascript)", ((__turbopack_context__) => {
"use strict";

__turbopack_context__.s([
    "default",
    ()=>DashboardPage
]);
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/node_modules/next/dist/server/route-modules/app-page/vendored/rsc/react-jsx-dev-runtime.js [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$components$2f$probability$2d$bar$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/components/probability-bar.tsx [app-rsc] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/frontend/lib/data.ts [app-rsc] (ecmascript)");
;
;
;
async function DashboardPage() {
    const [predictions, modelRun] = await Promise.all([
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["listPredictions"])(),
        (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$lib$2f$data$2e$ts__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["latestModelRun"])()
    ]);
    const chosenMetrics = modelRun.metrics[modelRun.chosen];
    const averageConfidence = predictions.reduce((total, prediction)=>total + prediction.confidence, 0) / Math.max(predictions.length, 1);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "page-stack",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "hero-card",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "eyebrow",
                        children: "Portfolio Surface"
                    }, void 0, false, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 13,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h1", {
                        children: "GOAL AI"
                    }, void 0, false, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 14,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                        className: "hero-copy",
                        children: "FIFA World Cup match prediction, team scouting notes, player analysis, and interpretable model diagnostics in one portfolio-quality frontend."
                    }, void 0, false, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 15,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/frontend/app/page.tsx",
                lineNumber: 12,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "card-grid card-grid--three",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "eyebrow",
                                children: "Chosen model"
                            }, void 0, false, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 23,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                children: modelRun.chosen.toUpperCase()
                            }, void 0, false, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 24,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "detail-list",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Test log-loss"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 27,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: chosenMetrics.test.logLoss.toFixed(3)
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 28,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 26,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Brier"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 31,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: chosenMetrics.test.brier.toFixed(3)
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 32,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 30,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Accuracy"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 35,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: [
                                                    (chosenMetrics.test.accuracy * 100).toFixed(1),
                                                    "%"
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 36,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 34,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 25,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 22,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "eyebrow",
                                children: "Predicted fixtures"
                            }, void 0, false, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 42,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                children: predictions.length
                            }, void 0, false, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 43,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "detail-list",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Model version"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 46,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: modelRun.version
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 47,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 45,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Outputs"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 50,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: "Home / Draw / Away"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 51,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 49,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 44,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 41,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("article", {
                        className: "panel",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "eyebrow",
                                children: "Average confidence"
                            }, void 0, false, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 57,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                children: [
                                    (averageConfidence * 100).toFixed(1),
                                    "%"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 58,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "detail-list",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Explainability"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 61,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: "SHAP top drivers"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 62,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 60,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "detail-row",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                children: "Data source"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 65,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                children: "Supabase or demo cache"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 66,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 64,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 59,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 56,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/frontend/app/page.tsx",
                lineNumber: 21,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("section", {
                className: "panel",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "section-heading",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "eyebrow",
                                        children: "Preview Grid"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 75,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                        children: "Upcoming / predicted fixtures"
                                    }, void 0, false, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 76,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 74,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                className: "section-copy",
                                children: "The migrated dashboard keeps the original fixture table while upgrading it to typed rendering and App Router navigation."
                            }, void 0, false, {
                                fileName: "[project]/frontend/app/page.tsx",
                                lineNumber: 78,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 73,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "table-wrap",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("table", {
                            className: "data-table",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("thead", {
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                children: "Home"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 85,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {}, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 86,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                children: "Away"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 87,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                children: "Probability mix"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 88,
                                                columnNumber: 17
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("th", {
                                                className: "align-right",
                                                children: "Confidence"
                                            }, void 0, false, {
                                                fileName: "[project]/frontend/app/page.tsx",
                                                lineNumber: 89,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/frontend/app/page.tsx",
                                        lineNumber: 84,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/frontend/app/page.tsx",
                                    lineNumber: 83,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("tbody", {
                                    children: predictions.slice(0, 20).map((prediction)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("tr", {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    children: prediction.home
                                                }, void 0, false, {
                                                    fileName: "[project]/frontend/app/page.tsx",
                                                    lineNumber: 95,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "table-muted",
                                                    children: "vs"
                                                }, void 0, false, {
                                                    fileName: "[project]/frontend/app/page.tsx",
                                                    lineNumber: 96,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    children: prediction.away
                                                }, void 0, false, {
                                                    fileName: "[project]/frontend/app/page.tsx",
                                                    lineNumber: 97,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "table-bar",
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$components$2f$probability$2d$bar$2e$tsx__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["ProbabilityBar"], {
                                                            pHome: prediction.pHome,
                                                            pDraw: prediction.pDraw,
                                                            pAway: prediction.pAway
                                                        }, void 0, false, {
                                                            fileName: "[project]/frontend/app/page.tsx",
                                                            lineNumber: 100,
                                                            columnNumber: 23
                                                        }, this)
                                                    }, void 0, false, {
                                                        fileName: "[project]/frontend/app/page.tsx",
                                                        lineNumber: 99,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/frontend/app/page.tsx",
                                                    lineNumber: 98,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$frontend$2f$node_modules$2f$next$2f$dist$2f$server$2f$route$2d$modules$2f$app$2d$page$2f$vendored$2f$rsc$2f$react$2d$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$rsc$5d$__$28$ecmascript$29$__["jsxDEV"])("td", {
                                                    className: "align-right",
                                                    children: [
                                                        (prediction.confidence * 100).toFixed(0),
                                                        "%"
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/frontend/app/page.tsx",
                                                    lineNumber: 107,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, prediction.id, true, {
                                            fileName: "[project]/frontend/app/page.tsx",
                                            lineNumber: 94,
                                            columnNumber: 17
                                        }, this))
                                }, void 0, false, {
                                    fileName: "[project]/frontend/app/page.tsx",
                                    lineNumber: 92,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/frontend/app/page.tsx",
                            lineNumber: 82,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/frontend/app/page.tsx",
                        lineNumber: 81,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/frontend/app/page.tsx",
                lineNumber: 72,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/frontend/app/page.tsx",
        lineNumber: 11,
        columnNumber: 5
    }, this);
}
}),
"[project]/frontend/app/page.tsx [app-rsc] (ecmascript, Next.js Server Component)", ((__turbopack_context__) => {

__turbopack_context__.n(__turbopack_context__.i("[project]/frontend/app/page.tsx [app-rsc] (ecmascript)"));
}),
"[externals]/next/dist/shared/lib/no-fallback-error.external.js [external] (next/dist/shared/lib/no-fallback-error.external.js, cjs)", ((__turbopack_context__, module, exports) => {

const mod = __turbopack_context__.x("next/dist/shared/lib/no-fallback-error.external.js", () => require("next/dist/shared/lib/no-fallback-error.external.js"));

module.exports = mod;
}),
];

//# sourceMappingURL=%5Broot-of-the-server%5D__0379ba53._.js.map