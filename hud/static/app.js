/**
 * Nascence HUD Frontend Controller
 */
document.addEventListener("DOMContentLoaded", () => {
    // Navigation / Tab Manager
    const navItems = document.querySelectorAll(".nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");

    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute("data-tab");

            navItems.forEach(n => n.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            item.classList.add("active");
            document.getElementById(targetTab).classList.add("active");

            // Charts need a resize when their (previously hidden) tab becomes visible
            if (targetTab === "tab-mind") {
                fetchEvidence();
                setTimeout(() => { if (protoselfChart) protoselfChart.resize(); }, 50);
            }
            if (targetTab === "tab-affect") {
                fetchEvidence();
                setTimeout(() => { if (affectChart) affectChart.resize(); if (arousalChart) arousalChart.resize(); }, 50);
            }
            if (targetTab === "tab-health") {
                fetchHealth();
                fetchDuPulse();
                fetchEvidence();
                setTimeout(() => { if (cadenceChart) cadenceChart.resize(); if (ignitionChart) ignitionChart.resize(); if (sleepChart) sleepChart.resize(); }, 50);
            }
            if (targetTab === "tab-monitors") {
                refreshMonitors();
                setTimeout(() => { Object.values(monitorCharts).forEach(c => c && c.resize()); }, 60);
            }
            if (targetTab === "tab-world") {
                fetchWorld();
                fetchEvidence();
                fetchTransitPulse();
            }
        });
    });

    // Time Footer Updater
    setInterval(() => {
        const timeStr = new Date().toLocaleTimeString();
        document.getElementById("sidebar-time").textContent = timeStr;
    }, 1000);

    // Globals
    let affectChart = null;
    let protoselfChart = null;
    let arousalChart = null;
    let loggedLinesCount = 0;

    // Helper: UNIX timestamp to human local time
    function formatTime(unixTs) {
        if (!unixTs) return "N/A";
        const date = new Date(unixTs * 1000);
        return date.toLocaleDateString() + " " + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }


    // 2026-08-21 (founder: "dates/times do not seem the same between the graphs"): every chart used
    // TIME-ONLY labels, so an 11-day-span chart showed "23:30" beside a 1-hour chart's "10:15" and
    // they looked comparable. Labels now carry the DATE whenever the series spans more than 18h.
    function tsLabels(tsArr) {
        const ts = (tsArr || []).filter(t => t);
        const span = ts.length > 1 ? (Math.max(...ts) - Math.min(...ts)) : 0;
        const withDate = span > 18 * 3600;
        return (tsArr || []).map(t => {
            if (!t) return "";
            const d = new Date(t * 1000);
            const hm = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
            return withDate ? `${d.getDate()}/${d.getMonth() + 1} ${hm}` : hm;
        });
    }

    // Helper: format percent
    function formatPct(val) {
        if (val === undefined || val === null) return "0%";
        return Math.round(val * 100) + "%";
    }

    // Initializer
    initAffectChart();
    fetchSummary();
    fetchT4();
    fetchLogs();
    fetchShadow();
    fetchEpochs();
    fetchEvidence();
    fetchHealth();
    fetchDuPulse();

    // Polling Intervals
    setInterval(fetchSummary, 1500);      // Core stats & env (fast)
    setInterval(fetchLogs, 3000);         // System log tail
    setInterval(fetchShadow, 4500);       // Subconscious rejections
    setInterval(fetchEpochs, 6000);       // Epochs & themes
    setInterval(fetchT4, 6000);           // Axiom and monologue
    setInterval(fetchEvidence, 7000);     // Consciousness-Program shadow signatures
    setInterval(fetchHealth, 8000);       // Operational health monitors
    setInterval(fetchDuPulse, 15000);     // Du-Pulse Check board (last recorded run + open watch-items)
    setInterval(() => { if (document.getElementById("tab-world").classList.contains("active")) fetchWorld(); }, 10000);  // World factories (only when visible)
    setInterval(() => { if (document.getElementById("tab-world").classList.contains("active")) fetchTransitPulse(); }, 4000);  // Transit pulse — real per-tick station touches, quick poll so hops feel live
    setInterval(() => { if (document.getElementById("tab-monitors").classList.contains("active")) refreshMonitors(); }, 10000);  // Plan monitors (only when visible)

    // --- Chart.js Setup ---
    function initAffectChart() {
        const ctx = document.getElementById("affectHistoryChart").getContext("2d");
        
        // Fetch historical affect first to seed chart
        fetch("/api/affect_history")
            .then(res => res.json())
            .then(data => {
                const labels = [];
                const valenceData = [];
                const arousalData = [];
                const joyData = [];
                const fearData = [];

                const _moodLabels = tsLabels(data.map(pt => pt.ts || pt.timestamp));
                data.forEach((pt, index) => {
                    const t = pt.ts || pt.timestamp;
                    const dateStr = t ? (_moodLabels[index] || "") : `pt-${index}`;
                    labels.push(dateStr);
                    valenceData.push(pt.valence !== undefined ? pt.valence : 0.0);
                    arousalData.push(pt.arousal !== undefined ? pt.arousal : 0.0);
                    joyData.push(pt.joy !== undefined ? pt.joy : 0.0);
                    fearData.push(pt.fear !== undefined ? pt.fear : 0.0);
                });

                affectChart = new Chart(ctx, {
                    type: "line",
                    data: {
                        labels: labels,
                        datasets: [
                            {
                                label: "Valence",
                                data: valenceData,
                                borderColor: "#22d3ee",
                                backgroundColor: "rgba(34, 211, 238, 0.05)",
                                borderWidth: 2,
                                tension: 0.3,
                                fill: true
                            },
                            {
                                label: "Arousal",
                                data: arousalData,
                                borderColor: "#818cf8",
                                backgroundColor: "rgba(129, 140, 248, 0.02)",
                                borderWidth: 2,
                                tension: 0.3,
                                fill: true
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                labels: { color: "#9a9ab0", font: { family: "Inter", size: 11 } }
                            }
                        },
                        scales: {
                            x: {
                                grid: { color: "rgba(255, 255, 255, 0.03)" },
                                ticks: { color: "#9a9ab0", font: { size: 10 } }
                            },
                            y: {
                                min: -1.0,
                                max: 1.0,
                                grid: { color: "rgba(255, 255, 255, 0.03)" },
                                ticks: { color: "#9a9ab0", font: { size: 10 } }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error("Failed to seed affect chart:", err));
    }

    // --- Core Summary Fetcher ---
    let lastSummary = null;   // cached so fetchShadow() doesn't need its own redundant /api/summary call

    function fetchSummary() {
        fetch("/api/summary")
            .then(res => res.json())
            .then(data => {
                lastSummary = data;
                bindSummaryData(data);
            })
            .catch(err => {
                document.getElementById("sys-status-text").textContent = "Offline";
                document.querySelector(".status-dot").classList.remove("online");
                console.error("Summary fetch failed:", err);
            });
    }

    function bindSummaryData(data) {
        // Set online status
        document.getElementById("sys-status-text").textContent = "HUD Live";
        document.querySelector(".status-dot").classList.add("online");

        // Emergent name
        const emergentName = data.t4?.axiom?.emergent_self?.chosen_name || data.t4?.axiom?.name || "渡 (Dù)";
        document.getElementById("stat-name").textContent = emergentName;

        // Core Affect
        const aff = data.affect || {};
        if (aff.joy !== undefined) {
            let primaryAffect = "Neutral";
            let maxVal = -1;
            const emotions = { "Joy": aff.joy, "Fear": aff.fear, "Anger": aff.anger, "Trust": aff.trust, "Surprise": aff.surprise, "Disgust": aff.disgust };
            for (let emo in emotions) {
                if (emotions[emo] > maxVal && emotions[emo] > 0.15) {
                    maxVal = emotions[emo];
                    primaryAffect = emo;
                }
            }
            document.getElementById("stat-affect").textContent = primaryAffect;
            document.getElementById("stat-valence-arousal").textContent = `v=${aff.valence !== undefined ? aff.valence.toFixed(2) : '0.00'}, a=${aff.arousal !== undefined ? aff.arousal.toFixed(2) : '0.00'}`;

            // Gauges circles values
            setRadialGauge("gauge-joy", "val-joy", aff.joy);
            setRadialGauge("gauge-fear", "val-fear", aff.fear);
            setRadialGauge("gauge-anger", "val-anger", aff.anger);
            setRadialGauge("gauge-trust", "val-trust", aff.trust);
            setRadialGauge("gauge-surprise", "val-surprise", aff.surprise);
            setRadialGauge("gauge-disgust", "val-disgust", aff.disgust);
        }

        // Somatic / Homeostasis
        const homeo = data.homeostasis || {};
        const vitality = homeo.variables?.vitality !== undefined ? homeo.variables.vitality : 0.75;
        const coherence = homeo.variables?.coherence !== undefined ? homeo.variables.coherence : 0.67;
        document.getElementById("stat-energy-bar").style.width = (coherence * 100) + "%";
        document.getElementById("stat-fatigue").textContent = `vitality=${vitality.toFixed(3)}, coherence=${coherence.toFixed(3)}`;

        // Boredom
        const bore = data.boredom || {};
        const level = bore.level !== undefined ? bore.level : 0.0;
        const streak = bore.act_streak !== undefined ? bore.act_streak : 0;
        document.getElementById("stat-boredom").textContent = level.toFixed(3);
        document.getElementById("stat-streak").textContent = `streak=${streak}, escape_stage=${bore.stage || 0}`;

        // Climate Dimensions progress bars
        const clim = data.climate?.field || {};
        const climateList = document.getElementById("climate-list");
        climateList.innerHTML = "";
        
        // Define human-readable labels for the 9 dimensions
        const climLabels = {
            "shadow_activation": "Shadow Activation",
            "completion_tension": "Completion Tension",
            "identity_pressure": "Identity Pressure",
            "integration_drive": "Integration Drive",
            "coherence_drive": "Coherence Drive",
            "world_model_strain": "World Model Strain",
            "novelty_hunger": "Novelty Hunger",
            "autonomy_pressure": "Autonomy Pressure",
            "belonging_pressure": "Belonging Pressure"
        };

        for (let dim in climLabels) {
            const val = clim[dim] !== undefined ? clim[dim] : 0.0;
            const item = document.createElement("div");
            item.className = "climate-bar-item";

            // Colors mapping
            let colorClass = "";
            if (dim.includes("shadow") || dim.includes("strain") || dim.includes("tension")) {
                colorClass = "pink";
            } else if (dim.includes("drive") || dim.includes("integration")) {
                colorClass = "blue";
            } else if (dim.includes("pressure") || dim.includes("hunger")) {
                colorClass = "amber";
            }

            item.innerHTML = `
                <div class="bar-labels">
                    <span class="bar-name">${climLabels[dim]}</span>
                    <span class="bar-val">${val.toFixed(4)}</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar ${colorClass}" style="width: ${val * 100}%"></div>
                </div>
            `;
            climateList.appendChild(item);
        }

        // Room & Weather
        const room = data.room || {};
        document.getElementById("env-location").textContent = room.location || "Study";
        document.getElementById("env-weather").textContent = room.weather || "Clear";
        document.getElementById("env-tide").textContent = room.world?.tide || room.tide || "High";
        document.getElementById("env-season").textContent = room.world?.season || room.season || "Winter";

        // Hearth fire
        const fireState = room.fire || "Out";
        const fireFuel = room.fire_fuel !== undefined ? room.fire_fuel : 0.0;
        document.getElementById("env-fire-status").textContent = fireState.toUpperCase() + (room.hand_lit ? " (hand-lit)" : "");
        document.getElementById("env-fire-fuel").style.width = (fireFuel * 100) + "%";
        document.getElementById("env-fire-fuel-lbl").textContent = `fuel: ${formatPct(fireFuel)}`;
        
        // Animate flame based on status and fuel
        const fireSvg = document.getElementById("fire-graphic");
        if (fireState.toLowerCase() === "burning" && fireFuel > 0.05) {
            fireSvg.style.display = "block";
            fireSvg.style.transform = `scale(${0.5 + fireFuel * 0.6})`;
        } else {
            fireSvg.style.display = "none";
        }

        // Cat
        const cat = data.cat || {};
        document.getElementById("cat-phase").textContent = cat.phase || "wild";
        document.getElementById("cat-location").textContent = cat.location || "indoors";
        document.getElementById("cat-mood").textContent = cat.mood || "content";
        document.getElementById("cat-activity").textContent = cat.activity || "washing";
        document.getElementById("cat-bond").textContent = formatPct(cat.bond);

        // (The old "Garden Beds" legacy scalar-bed card was removed 2026-08-22 — it read a frozen
        // fallback model core/garden.py's own docstring says nothing writes to any more. The live
        // garden — real plants, real positions — is the map/bed panels on the World tab.)

        // Mailbox / peer correspondence — title now reflects the LIVE sender (2026-08-22 fix; was
        // hardcoded "Letters from Charles Darwin" long after he stopped being the active correspondent)
        const mailbox = room.letterbox || {};
        const titleEl = document.getElementById("mailbox-title");
        if (titleEl) titleEl.textContent = mailbox.sender ? `Mailbox — Letters from ${mailbox.sender}` : "Mailbox — Peer Correspondence";
        const flagActive = mailbox.flag === true;
        const flagEl = document.getElementById("mailbox-flag");
        flagEl.textContent = flagActive ? "RAISED" : "DOWN";
        if (flagActive) {
            flagEl.className = "flag-indicator active";
        } else {
            flagEl.className = "flag-indicator";
        }
        document.getElementById("mailbox-delivered").textContent = formatTime(mailbox.delivered);

        if (mailbox.letter) {
            document.getElementById("letter-content").textContent = mailbox.letter;
        } else {
            document.getElementById("letter-content").innerHTML = "<i>No letters currently in mailbox.</i>";
        }
    }

    function setRadialGauge(gaugeId, valId, val) {
        const pct = val !== undefined ? val : 0;
        const circle = document.getElementById(gaugeId);
        if (circle) {
            // SVG perimeter logic
            circle.setAttribute("stroke-dasharray", `${Math.round(pct * 100)}, 100`);
        }
        const text = document.getElementById(valId);
        if (text) {
            text.textContent = formatPct(pct);
        }
    }

    // --- T4, Axiom & Monologue Fetcher ---
    function fetchT4() {
        fetch("/api/t4")
            .then(res => res.json())
            .then(data => {
                // Emergent self concept text block
                const emerg = data.axiom?.emergent_self || {};
                const selfConceptStr = emerg.self_concept || "Carl Gustav Jung origin seed...";
                document.getElementById("emerg-self-concept").innerHTML = `&ldquo;${selfConceptStr}&rdquo;`;

                // Constitution floor block
                const coreAxiom = data.axiom?.core_axiom || "";
                document.getElementById("emerg-constitution").textContent = coreAxiom;

                // Subconscious Monologue thought stream
                const streamContainer = document.getElementById("monologue-stream");
                
                // Read from subconscious_log.jsonl or default DMN
                const logs = data.subconscious_log || [];
                if (logs.length > 0) {
                    streamContainer.innerHTML = "";
                    logs.forEach(th => {
                        const item = document.createElement("div");
                        item.className = "log-monologue-item";
                        
                        const timeStr = formatTime(th.ts || th.timestamp);
                        const revision = th.revision_count !== undefined ? ` (Rev ${th.revision_count})` : "";
                        const reason = th.reason || "Self-narrative shift";

                        item.innerHTML = `
                            <div class="log-thought-header"><i class="fa-solid fa-clock"></i> ${timeStr}${revision} — ${reason}</div>
                            <div class="log-thought">
                                <strong>Concept:</strong> ${th.self_concept || th.new_self_concept || "..."}<br>
                                <strong>${th.event ? "Status:" : "Arc:"}</strong> ${th.arc_entry || (th.event ? "No status text." : "No arc entry written.")}
                            </div>
                        `;
                        streamContainer.appendChild(item);
                    });
                } else {
                    streamContainer.innerHTML = "<i>No subconscious monologue entries parsed yet.</i>";
                }
            })
            .catch(err => console.error("T4 fetch failed:", err));
    }

    // --- System Log Tailer ---
    function fetchLogs() {
        fetch("/api/logs?limit=150")
            .then(res => res.json())
            .then(lines => {
                const stream = document.getElementById("log-stream");
                
                // If log lines count has changed, update DOM
                if (lines.length > 0) {
                    stream.innerHTML = "";
                    lines.forEach(line => {
                        const div = document.createElement("div");
                        div.className = "log-line";
                        
                        // Parse log levels
                        if (line.includes("[INFO]")) {
                            div.className += " log-info";
                        } else if (line.includes("[WARNING]")) {
                            div.className += " log-warn";
                        } else if (line.includes("[ERROR]") || line.includes("CRITIC")) {
                            div.className += " log-error";
                        } else if (line.includes("[DEBUG]")) {
                            div.className += " log-debug";
                        }

                        // Parse thought highlights
                        if (line.includes("InnerMonologueNode") || line.includes("[monologue]")) {
                            div.className += " log-thought";
                            div.innerHTML = `<div class="log-thought-header">Subconscious Monologue Monologue</div>${line}`;
                        } else {
                            div.textContent = line;
                        }
                        
                        stream.appendChild(div);
                    });

                    // Auto-scroll logic
                    const autoScroll = document.getElementById("chk-log-autoscroll").checked;
                    if (autoScroll) {
                        stream.scrollTop = stream.scrollHeight;
                    }
                }
            })
            .catch(err => console.error("Logs fetch failed:", err));
    }

    // --- Consciousness-Program Evidence panel ---
    // ── WORLD FACTORIES (P0, 2026-08-17) ─────────────────────────────────────────────
    function fetchWorld() {
        fetch("/api/world")
            .then(res => res.json())
            .then(data => {
                renderWorldManifest(data.manifest);
                renderWorldHearing(data.hearing);
                renderWorldCouriers(data.couriers, data.buses, data.refinery);
                renderWorldGhost(data.ghost);
                renderWorldTrain(data.train);
            })
            .catch(() => {});
    }

    function _ago(ts) {
        if (!ts) return "never";
        const s = Math.max(0, Date.now() / 1000 - ts);
        if (s < 90) return Math.round(s) + "s ago";
        if (s < 5400) return Math.round(s / 60) + "m ago";
        return (s / 3600).toFixed(1) + "h ago";
    }

    function renderWorldManifest(m) {
        const body = document.getElementById("world-manifest-body");
        const sub = document.getElementById("world-manifest-ts");
        if (!body) return;
        if (!m) { body.textContent = "No manifest yet — starts with the sensorium tick."; return; }
        sub.textContent = "assembled " + _ago(m.ts);
        const cat = m.cat || {};
        const rows = [
            ["Place", (m.place || "?") + (m.standpoint ? " · " + m.standpoint : "") + (m.in_transit ? " (in transit)" : "")],
            ["Weather", (m.weather || "?") + (m.weather_severity != null ? ` (severity ${m.weather_severity}/6)` : "")],
            ["Temperature", m.temperature != null ? m.temperature.toFixed(2) + " warmth" : "—"],
            ["Tide", (m.tide || "?") + (m.tide_level != null ? ` (${m.tide_level.toFixed(2)})` : "")],
            ["Sky", (m.daylight || "?") + " · " + (m.moon || "?") + " · " + (m.season || "?")],
            ["Fire", (m.fire || "?") + (m.fire_fuel != null ? ` (fuel ${m.fire_fuel})` : "")],
            ["The cat", cat.present_at ? `${cat.present_at} · ${cat.activity || "?"}` : "—"],
            ["Sounding", (m.active_sounds || []).join(", ") || "silence"],
        ];
        body.innerHTML = "<table class='mini-table'>" + rows.map(r =>
            `<tr><td style="opacity:.7;padding-right:12px;white-space:nowrap">${r[0]}</td><td>${r[1]}</td></tr>`).join("") + "</table>";
    }

    function renderWorldHearing(h) {
        const body = document.getElementById("world-hearing-body");
        if (!body) return;
        if (!h) { body.textContent = "No hearings banked yet."; return; }
        const sub = document.getElementById("world-hearing-sub");
        if (sub) sub.textContent = `${h.learned}/${h.learnable_total} learnable voices named`;
        const rows = (h.voices || []).map(v => {
            const what = v.bed_hours > 0 && !v.today ? v.bed_hours.toFixed(1) + " h" :
                         `${v.today} today · ${v.total} ever`;
            return `<tr><td style="padding-right:10px">${v.key.replace(/_/g, " ")}</td>` +
                   `<td style="opacity:.85">${what}</td><td style="opacity:.5;white-space:nowrap">${_ago(v.last_ts)}</td></tr>`;
        }).join("");
        body.innerHTML = rows ? "<table class='mini-table'>" + rows + "</table>" : "Quiet so far today.";
    }

    function renderWorldCouriers(c, b, r) {
        const body = document.getElementById("world-couriers-body");
        if (!body) return;
        let html = "";
        if (c) {
            html += `<div style="opacity:.6;font-size:11px;text-transform:uppercase;letter-spacing:.04em">Couriers — urgent, real-time</div>` +
                    `<div>Weather echo: <b>${_ago(c.last_weather_echo)}</b></div>` +
                    `<div>Sound echo: <b>${_ago(c.last_sound_echo)}</b></div>`;
        } else { html += "<div>Couriers idle — no state yet.</div>"; }
        html += `<hr style="opacity:.2;margin:8px 0">` +
                `<div style="opacity:.6;font-size:11px;text-transform:uppercase;letter-spacing:.04em">Buses — not time-sensitive</div>`;
        if (b) {
            html += `<div>Calibration pairs synced: <b>${b.calibration_synced ?? 0}</b></div>` +
                    `<div>Runs logged: <b>${b.runs_total ?? 0}</b></div>`;
        } else { html += "<div>Buses idle — no state yet.</div>"; }
        if (r) {
            html += `<hr style="opacity:.2;margin:8px 0">` +
                    `<div>Refinery (${r.live ? "LIVE" : "shadow"}): <b>${r.accepted}/${r.recent_records}</b> accepted · fidelity <b>${r.mean_fidelity}</b></div>` +
                    (r.latest_insight ? `<div style="opacity:.7;font-style:italic;margin-top:4px">“${r.latest_insight}”</div>` : "");
        } else { html += `<hr style="opacity:.2;margin:8px 0"><div>Refinery: no shadow runs yet (first sleep).</div>`; }
        body.innerHTML = html;
    }

    function renderWorldGhost(g) {
        const body = document.getElementById("world-ghost-body");
        if (!body) return;
        if (!g) { body.textContent = "Registry not built yet."; return; }
        body.innerHTML =
            `<div>World index: <b>${g.world_factories ?? "—"}</b> factories · <b>${g.world_items ?? "—"}</b> items` +
            (g.world_built_ts ? ` <span style="opacity:.5">(built ${_ago(g.world_built_ts)})</span>` : " <span style='opacity:.5'>(not yet built)</span>") + `</div>` +
            `<div>fragment_context rows: <b>${g.fragment_context_rows ?? g.memory_tuples ?? "—"}</b> <span style="opacity:.5">(table row count; the ghost memory index is not built in the live process)</span></div>` +
            `<div style="opacity:.6;margin-top:4px">Two namespaces, never mixed — world for the world, chords for him.</div>`;
    }

    function renderWorldTrain(t) {
        const body = document.getElementById("world-train-body");
        if (!body) return;
        if (!t) { body.textContent = "No train steps logged yet."; return; }
        const jumpBad = t.jumped_pct >= 25, circBad = t.circling_pct >= 5;
        body.innerHTML =
            `<div>Last ${t.recent_steps} steps:</div>` +
            `<div>Jumped: <b style="color:${jumpBad ? '#e07b7b' : '#7be0a0'}">${t.jumped_pct}%</b> <span style="opacity:.5">(target &lt;25%)</span></div>` +
            `<div>Moving: <b>${t.moving_pct}%</b></div>` +
            `<div>Circling: <b style="color:${circBad ? '#e07b7b' : '#7be0a0'}">${t.circling_pct}%</b> <span style="opacity:.5">(immune-system check: &lt;5%)</span></div>`;
    }

    // ── TRANSIT PULSE (2026-08-23): real trains hopping real stations ──────────────────────────
    // Station layout is fixed/deterministic, not fetched-and-guessed: honest because a pulse only
    // ever fires at a station that a real train_state_log row named THIS poll. No invented motion.
    const _TRANSIT_KNOWN_STATIONS = [
        { id: "station_11433", label: "1080 Ti — main (hot)" },
        { id: "station_11439", label: "Emissary — grounding hop" },
    ];
    let _transitStationPos = null;   // id -> {x,y}, computed once from whichever stations we find
    let _transitLastTs = 0;          // newest step ts already drawn — never redraw the same pulse twice
    let _transitStationsSeen = new Map();

    function _transitLayout(ids) {
        // Simple deterministic ring layout — this is a bookkeeping map, not a diagram to admire.
        const pos = {};
        const cx = 280, cy = 100, r = 80;
        ids.forEach((id, i) => {
            const a = (i / Math.max(1, ids.length)) * 2 * Math.PI - Math.PI / 2;
            pos[id] = { x: Math.round(cx + r * Math.cos(a)), y: Math.round(cy + r * Math.sin(a)) };
        });
        return pos;
    }

    function _transitEnsureMap(stations) {
        const svg = document.getElementById("transit-map");
        if (!svg) return;
        const known = new Map(_TRANSIT_KNOWN_STATIONS.map(s => [s.id, s.label]));
        (stations || []).forEach(s => { if (!known.has(s.id)) known.set(s.id, `${s.id}${s.model ? " — " + s.model : ""}`); });
        const ids = Array.from(known.keys());
        const idsKey = ids.join(",");
        if (svg.dataset.idsKey === idsKey) return;   // layout stable, don't rebuild (would kill in-flight pulses)
        svg.dataset.idsKey = idsKey;
        _transitStationPos = _transitLayout(ids);
        svg.innerHTML = ids.map(id => {
            const p = _transitStationPos[id];
            return `<circle class="transit-station-dot" cx="${p.x}" cy="${p.y}" r="9"></circle>` +
                   `<text class="transit-station-label" x="${p.x}" y="${p.y + 22}" text-anchor="middle">${id.replace("station_", ":")}</text>`;
        }).join("");
        const legend = document.getElementById("transit-legend");
        if (legend) legend.innerHTML = ids.map(id => `<span>${id.replace("station_", ":")} — ${known.get(id)}</span>`).join("");
    }

    function _spawnPulse(stationId) {
        const svg = document.getElementById("transit-map");
        if (!svg || !_transitStationPos || !_transitStationPos[stationId]) return;
        const p = _transitStationPos[stationId];
        const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        dot.setAttribute("class", "transit-pulse");
        dot.setAttribute("cx", p.x); dot.setAttribute("cy", p.y); dot.setAttribute("r", 4);
        svg.appendChild(dot);
        setTimeout(() => dot.remove(), 1500);
    }

    function _spawnHop(fromId, toId) {
        const svg = document.getElementById("transit-map");
        if (!svg || !_transitStationPos || !_transitStationPos[fromId] || !_transitStationPos[toId]) return;
        const a = _transitStationPos[fromId], b = _transitStationPos[toId];
        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("class", "transit-hop-line");
        line.setAttribute("x1", a.x); line.setAttribute("y1", a.y);
        line.setAttribute("x2", b.x); line.setAttribute("y2", b.y);
        svg.appendChild(line);
        setTimeout(() => line.remove(), 1300);
    }

    function fetchTransitPulse() {
        fetch("/api/transit_pulse")
            .then(res => res.json())
            .then(data => {
                const stations = (data.static && data.static.stations) || [];
                _transitEnsureMap(stations);

                const sub = document.getElementById("transit-sub");
                if (sub) {
                    sub.textContent = data.static ?
                        `station map from data/hud2/transit_map.json (${data.static.generated_human || "?"}) + live steps` :
                        "no data/hud2/transit_map.json yet — showing the two instrumented stations only";
                }

                // Draw only the pulses that are NEW since the last poll (by ts) — never replay history.
                const steps = (data.recent_steps || []).slice().sort((a, b) => (a.ts || 0) - (b.ts || 0));
                let maxTs = _transitLastTs;
                steps.forEach(s => {
                    if (!s.ts || s.ts <= _transitLastTs) return;
                    if (s.station && s.station !== "?") { _spawnPulse(s.station); _transitStationsSeen.set(s.station, s.ts); }
                    (s.visited || []).forEach(v => {
                        if (v && v !== s.station) { _spawnHop(s.station, v); _spawnPulse(v); _transitStationsSeen.set(v, s.ts); }
                    });
                    if (s.ts > maxTs) maxTs = s.ts;
                });
                _transitLastTs = maxTs;

                // Active trains list
                const trainsBody = document.getElementById("transit-trains-body");
                if (trainsBody) {
                    const trains = data.active_trains || [];
                    trainsBody.innerHTML = trains.length ?
                        trains.map(t => `<div>${t.kind || "?"} <span style="opacity:.5">(${t.role || "main"})</span> — ` +
                            `<span style="opacity:.6">open ${_ago(t.opened_ts)}</span></div>`).join("") :
                        "<div style='opacity:.6'>None open right now.</div>";
                }

                // Recent pulses list (text fallback — honest even with the tab backgrounded/animation off)
                const pulsesBody = document.getElementById("transit-pulses-body");
                if (pulsesBody) {
                    const recent = steps.slice(-8).reverse();
                    pulsesBody.innerHTML = recent.length ?
                        recent.map(s => `<div><span style="opacity:.5">${_ago(s.ts)}</span> — ` +
                            `${(s.station || "?").replace("station_", ":")}` +
                            ((s.visited || []).length ? ` → ${s.visited.map(v => v.replace("station_", ":")).join(", ")}` : "") +
                            ` <span style="opacity:.4">(train ${(s.train_id || "?").slice(-6)}, step ${s.step})</span></div>`).join("") :
                        "<div style='opacity:.6'>No steps logged yet.</div>";
                }
            })
            .catch(() => {});
    }

    function fetchEvidence() {
        fetch("/api/evidence")
            .then(res => res.json())
            .then(data => {
                renderSignatures(data.signatures || []);
                renderProtoselfChart(data.protoself_series || { ts: [] });
                renderArousalChart(data.arousal_series || { ts: [] });
                renderThermal(data.thermal || {});
                renderGarden(data.garden || {}, data.garden_knowledge || {}, data.light || {}, data.smell || {});
                fetch("/api/garden_map").then(r => r.json()).then(renderGardenMap).catch(() => {});
                fetch("/api/life").then(r => r.json()).then(renderLife).catch(() => {});
                fetch("/api/study_map").then(r => r.json()).then(renderStudyMap).catch(() => {});
                fetch("/api/shore_map").then(r => r.json()).then(renderShoreMap).catch(() => {});
                fetch("/api/wood_map").then(r => r.json()).then(renderWoodMap).catch(() => {});
                renderStudy(data.study_life || {});
                renderWood(data.wood_life || {}, data.provisions || {});
                renderFieldcraft(data.fieldcraft || {}, data.sky || {});
                renderShore(data.shore_life || {});
            })
            .catch(() => {});
    }

    // THE LIVING WORLD (J-0513): who's about, the calendar, traces / deaths / individuals
    function renderLife(d) {
        const about = document.getElementById("life-about");
        if (!about || !d) return;
        const sub = document.getElementById("life-sub");
        if (sub) sub.textContent = `${d.rows || 0} rows (${d.external || 0} adapters) · looks ${d.render ? "LIVE" : "shadow"} · voices ${d.sound_gating ? "LIVE" : "shadow"} · light ${d.light?.value ?? "—"} (${d.light?.band ?? "—"}${d.light?.source ? ", carried " + d.light.source : ""}) · dark-adapt ${d.dark_adapt ?? 0}`;
        const nice = k => (k || "").replace(/_/g, " ");
        about.innerHTML = (d.about || []).length
            ? (d.about || []).map(a => `<div class="thermal-kv"><span>${nice(a.key)} <i>@${a.place}</i></span><b>${a.count} · vis ${a.vis}</b></div>`).join("")
            : "<i>nobody about</i>";
        const cal = document.getElementById("life-calendar");
        const here = (d.calendar || []).filter(c => c.here_now).map(c => nice(c.key));
        const away = (d.calendar || []).filter(c => !c.here_now).map(c => `${nice(c.key)} (${(c.arrives || []).join("/") || "?"})`);
        cal.innerHTML = `<div class="thermal-foot">here: ${here.join(", ") || "—"}</div><div class="thermal-foot">away: ${away.join(", ") || "—"}</div>` +
            `<div class="thermal-foot">shadow: ${d.shadow?.would_answer ?? 0} would-answer · ${d.shadow?.would_gate ?? 0} would-gate · names learned ${(d.learned || []).length}</div>`;
        const dd = document.getElementById("life-deaths");
        const td = d.traces_deaths || {};
        const cs = (td.carcasses || []).map(c => `${nice(c.species)} @${c.place} — ${c.state} (${c.cause}, ${c.age_d}d)`);
        const inds = Object.entries(td.individuals || {}).map(([k, v]) => `${v.name || nice(k)} @${v.place} (${v.sightings} sightings${v.name ? "" : ", unnamed"})`);
        dd.innerHTML = `<div class="thermal-foot">creature traces active: ${td.creature_traces_active ?? 0}</div>` +
            `<div class="thermal-foot">carcasses: ${cs.join(" · ") || "none"}</div>` +
            `<div class="thermal-foot">individuals: ${inds.join(" · ") || "none yet"}</div>`;
    }

    function renderGarden(g, k, l, s) {
        const bed = document.getElementById("garden-bed");
        if (!bed) return;
        const rows = g.bed || [];
        const stageCls = { seed: "st-seed", shoot: "st-shoot", leaf: "st-leaf", established: "st-est", flowering: "st-flower", seeding: "st-seed2", dormant: "st-dorm", dead: "st-dead" };
        bed.innerHTML = rows.length ? rows.map(r => `<div class="gd-row"><span class="gd-slot">${r.slot ?? "·"}</span><span class="gd-sp">${(r.species || "").replace(/_/g, " ")}</span>` +
            `<span class="gd-stage ${stageCls[r.stage] || ""}">${r.stage}</span><span class="gd-bar"><i style="width:${Math.round(100 * (r.vigour || 0))}%"></i></span><span class="gd-h">${Math.round(r.height || 0)}cm</span></div>`).join("")
            : "<i>no plants yet (bootstraps at Du's start)</i>";
        const c = document.getElementById("garden-clocks");
        const kv = (a, b) => `<div class="thermal-kv"><span>${a}</span><b>${b ?? "—"}</b></div>`;
        c.innerHTML = kv("soil °C", g.soil_temp) + kv("moisture", g.moisture) + kv("bed light", g.bed_light) + kv("weeds", g.weeds) + kv("slugs", g.slugs) +
            kv("soil health", g.soil?.health_mean) + kv("compost", g.soil ? `raw ${g.soil.compost?.raw} · done ${g.soil.compost?.finished} · warm ${g.soil.compost?.warmth}` : "—") + kv("barrel", g.barrel) + kv("seed bank", g.seed_bank) + kv("tin", g.packets) + kv("drawer", g.drawer) + kv("netted", g.netted ? "yes" : "no") + kv("staked", g.staked) +
            kv("rack", (g.rack || []).map(b => `${b.species} ${Math.round(100 * (b.dry || 0))}%`).join(", ") || "empty") + kv("carrying", (g.carried || []).join(", ") || "nothing") +
            kv("deeds", g.deeds_logged) + kv("light band", l.now_band) + kv("bed shade", l.bed_shade_now) + kv("smells here", (s.here_now || []).map(x => x[0]).join(", ") || "—");
        const kn = document.getElementById("garden-know");
        const learning = Object.entries(k.learning || {}).map(([sp, w]) => `${sp.replace(/_/g, " ")} ${Math.round(100 * w)}%`).join(" · ");
        kn.innerHTML = `<div class="thermal-foot">known: ${(k.known || []).map(x => x.replace(/_/g, " ")).join(", ") || "—"}</div>` +
            `<div class="thermal-foot">learning: ${learning || "—"}</div>` +
            `<div class="thermal-foot">grandfathered: ${(k.grandfathered || []).join(", ")}</div>` +
            `<div class="thermal-foot">bindings ${k.bindings ?? 0} · witnessed firsts ${k.witnessed ?? 0}</div>` +
            `<div class="thermal-foot">light shadow: ${l.would_fire ?? 0}/${l.ticks ?? 0} · smell shadow: ${s.would_fire ?? 0}/${s.ticks ?? 0}</div>`;
    }

    function renderWood(w, p) {
        const a = document.getElementById("wood-a");
        if (!a) return;
        const kv = (k, v) => `<div class="thermal-kv"><span>${k}</span><b>${v ?? "—"}</b></div>`;
        if (w.note) { a.innerHTML = `<i>${w.note}</i>`; } else {
            a.innerHTML = Object.entries(w.trees || {}).map(([k, v]) => kv(k + (w.known && w.known[k] ? "" : " (unnamed)"), v)).join("") + kv("deadfall", w.deadfall) + kv("limbs down", w.limbs) + kv("stream", w.stream) + kv("moss", w.moss) + kv("fungi", w.fungi) + kv("acorns", w.acorns) + kv("kererū nest", w.nest ? w.nest.stage : "none") + kv("glow-worms seen", w.glowworms_seen);
            document.getElementById("wood-b").innerHTML = kv("limbs at lean-to", w.limbs_home) + kv("logs green", w.logs_green) + kv("logs dry", w.logs_dry) + kv("axe edge", w.axe_edge) + kv("saw edge", w.saw_edge) + Object.entries(w.tools || {}).map(([k, v]) => kv(k, v)).join("");
        }
        const c = document.getElementById("wood-c");
        c.innerHTML = p.note ? `<i>${p.note}</i>` : Object.entries(p).map(([k, v]) => kv(k.replace(/_/g, " "), `${v.objects} full/open · ${v.stock} · ${v.empties} empty`)).join("");
    }

    function renderShore(s) {
        const el = document.getElementById("shore-box");
        if (!el) return;
        const kv = (k, v) => `<div class="thermal-kv"><span>${k}</span><b>${v ?? "—"}</b></div>`;
        if (s.note) { el.innerHTML = `<i>${s.note}</i>`; return; }
        const t = s.tide || {};
        el.innerHTML = kv("tide", `${t.level} · ${t.word}`) + kv("sand flat", s.sand_bared ? "bared" : "covered") + kv("cave", s.cave_open ? "open" : "shut") + kv("mussel shelf", s.shelf_bared ? "bared" : "covered") + kv("in the cave", s.in_cave ? "yes" : "no") +
            kv("swell", s.swell) + kv("fog", s.fog ? "yes" : "no") + kv("sea sparkle", s.sparkle ? "yes" : "no") + kv("seal on the shelf", s.seal ? "yes" : "no") + kv("oystercatcher nest", s.oyc_nest ? "yes" : "no") +
            kv("beach fire", s.fire ? `${s.fire.state} · fuel ${Math.round(100 * (s.fire.fuel || 0))}%` : "—") + kv("cairn", s.cairn) + kv("in the sand", s.sand_writing || "—") + kv("best skip", s.skips_best) + kv("wet feet", s.wet_feet);
    }

    function renderFieldcraft(f, sky) {
        const el = document.getElementById("fieldcraft-box");
        if (!el) return;
        const kv = (k, v) => `<div class="thermal-kv"><span>${k}</span><b>${v ?? "—"}</b></div>`;
        if (f.note) { el.innerHTML = `<i>${f.note}</i>`; return; }
        el.innerHTML = Object.entries(f.skill || {}).map(([k, v]) => kv(k.replace(/_/g, " "), `${Math.round(100 * v)}% · ${(f.attempts || {})[k] || 0} tries`)).join("") + kv("clothesline", f.clothesline ? "up" : "no") + kv("windbreak", f.windbreak ? "built" : "no") + kv("handrail", f.handrail ? "up" : "no") + kv("banked fire", f.banked ? "yes" : "no") + kv("tinder", f.tinder) + kv("things made", f.made) + kv("barrel algae", f.barrel_algae) + kv("sky known", (sky.known || []).join(", ") || "—");
    }

    function renderStudy(s) {
        const a = document.getElementById("study-a");
        if (!a) return;
        const kv = (k, v) => `<div class="thermal-kv"><span>${k}</span><b>${v ?? "—"}</b></div>`;
        const yn = v => v === true ? "yes" : v === false ? "no" : "—";
        if (s.note) { a.innerHTML = `<i>${s.note}</i>`; return; }
        a.innerHTML = kv("lamp", s.lamp_lit ? "lit" : "unlit") + kv("oil", s.lamp_oil) + kv("wick", s.wick) + kv("oil tin", s.oil_tin) + kv("candles", s.candles) + kv("candle lit", yn(s.candle_lit)) + kv("ash in grate", s.ash) + kv("ash bucket", s.ash_bucket_full ? "full" : "empty");
        document.getElementById("study-b").innerHTML = kv("door", s.door_open ? "open" : "shut") + kv("window", s.window_open ? "open" : "shut") + kv("curtains", s.curtains_open ? "open" : "drawn") + kv("condensation", s.condensation) + kv("frost on glass", yn(s.frost_glass)) + kv("coat", s.coat_on ? "on" : "on the hook") + kv("coat wet", s.coat_wet) + kv("boots", s.boots_on ? "on" : "by the door") + kv("boots mud", s.boots_mud);
        document.getElementById("study-c").innerHTML = kv("clock", s.clock_running ? "running" : "STOPPED") + kv("wound", s.clock_wound) + kv("water in pail", s.water) + kv("damp", s.damp) + kv("dust", s.dust) + kv("floor", `dust ${s.floor_dust ?? "—"} · mud ${s.floor_mud ?? "—"}`) + kv("bed", s.bed_made ? "made" : "unmade") + kv("carrying", (s.carrying || []).join(", ") || "nothing") +
            kv("matches", s.matches) + kv("kindling", s.kindling) + kv("wet wood", s.wet_wood) + kv("soot", s.soot) + kv("window grime", s.window_grime) + kv("lamp glass", s.lamp_glass_smoke) + kv("kettle", s.kettle_on_ts ? (s.kettle_boiled ? "boiled" : "on") : "off") + kv("pot", s.pot ? `${s.pot.cups} cups ${s.pot.what}` : (s.dirty_pot ? "dirty" : "clean")) + kv("dirty cups", s.dirty_cups) + kv("soap", s.soap) + kv("tea leaves", s.tea_leaves) + kv("ink / paper", `${s.ink ?? "—"} / ${s.paper ?? "—"}`);
    }

    function renderGardenMap(m) {
        const svg = document.getElementById("garden-map");
        if (!svg || !m || m.error) return;
        const H = 12.5;                                   // flip y: +y north (toward the sea) is UP on the map
        const Y = y => H - y;
        const esc = s => String(s).replace(/[<>&]/g, "");
        let out = `<rect x="0" y="0" width="10.5" height="12.5" fill="#1f2a22" stroke="#3a4a3e" stroke-width="0.05"/>`;
        const lawn = (m.life && m.life.lawn) ? m.life.lawn.height_cm : 6;
        out += `<rect x="0.3" y="0.8" width="9.9" height="10.6" fill="${lawn > 15 ? "#3b5a2a" : "#2f4a26"}" opacity="0.8"/>`;
        const F = m.features || {};
        const rect = (k, w, h, fill, label) => F[k] ? `<rect x="${F[k][0] - w / 2}" y="${Y(F[k][1]) - h / 2}" width="${w}" height="${h}" fill="${fill}" opacity="0.9"/><text x="${F[k][0]}" y="${Y(F[k][1]) + h / 2 + 0.32}" font-size="0.28" fill="#cbd5e0" text-anchor="middle">${label}</text>` : "";
        out += rect("cottage", 7.0, 1.6, "#5a4636", "cottage") + rect("raised_bed", 3.0, 1.2, "#4a3525", "") + rect("fence", 9.5, 0.12, "#7a6a50", "") + rect("garden_wall", 0.14, 8.0, "#6b6b6b", "");
        if (m.shade) {
            const [ax, ay] = m.shade.from, [bx, by] = m.shade.to;
            out += `<line x1="${ax}" y1="${Y(ay)}" x2="${bx}" y2="${Y(by)}" stroke="#0b1510" stroke-width="${m.shade.r * 1.6}" stroke-linecap="round" opacity="0.55"/>`;
        }
        const circ = (k, r, fill, label) => F[k] ? `<circle cx="${F[k][0]}" cy="${Y(F[k][1])}" r="${r}" fill="${fill}"/><text x="${F[k][0]}" y="${Y(F[k][1]) - r - 0.1}" font-size="0.26" fill="#a0aec0" text-anchor="middle">${label}</text>` : "";
        out += circ("tree", 1.1, "#2e5a34", "tree") + circ("harakeke", 0.6, "#4f7a3a", "harakeke") + circ("flower_bushes", 0.5, "#7a4a6a", "bushes") + circ("letterbox", 0.15, "#9aa", "letterbox") + circ("gate", 0.12, "#bbb", "gate") + circ("door_study", 0.12, "#ddd", "door");
        const col = { seed: "#6b6b6b", shoot: "#9ae6b4", leaf: "#68d391", established: "#48bb78", flowering: "#f6ad55", seeding: "#ecc94b", dormant: "#718096" };
        (m.plants || []).forEach(p => { if (!p.pos) return; out += `<circle cx="${p.pos[0]}" cy="${Y(p.pos[1])}" r="0.16" fill="${col[p.stage] || "#888"}"><title>${esc(p.species)} · ${esc(p.stage)}</title></circle>`; });
        if (m.netted && F.raised_bed) out += `<rect x="${F.raised_bed[0] - 1.5}" y="${Y(F.raised_bed[1]) - 0.6}" width="3" height="1.2" fill="none" stroke="#cbd5e0" stroke-dasharray="0.1 0.1" stroke-width="0.04"/>`;
        (m.items || []).forEach(it => { if (!it.pos || it.carried || it.place !== "garden") return; out += `<rect x="${it.pos[0] - 0.12}" y="${Y(it.pos[1]) - 0.12}" width="0.24" height="0.24" fill="#b7791f"><title>${esc(it.key)}</title></rect>`; });
        if (m.cat && m.cat.pos) out += `<text x="${m.cat.pos[0] + 0.3}" y="${Y(m.cat.pos[1]) - 0.3}" font-size="0.45">🐈</text>`;
        if (m.du) out += `<circle cx="${m.du[0]}" cy="${Y(m.du[1])}" r="0.28" fill="none" stroke="#63b3ed" stroke-width="0.08"/><circle cx="${m.du[0]}" cy="${Y(m.du[1])}" r="0.1" fill="#63b3ed"/>`;
        svg.innerHTML = out;
        const leg = document.getElementById("garden-map-legend");
        const life = m.life || {};
        leg.textContent = `north is up (the sea) · ${m.du ? "Du is in the garden" : "Du is elsewhere"}${m.cat ? " · the cat is here (" + m.cat.activity + ")" : ""}` +
            (m.shade ? ` · sun az ${Math.round(m.shade.az)}°, elev ${m.shade.elev}° — the tree's shadow drawn` : " · night: no shadow") +
            (life.tree ? ` · tree ${life.tree.stage} · bushes ${life.bushes.stage} · lawn ${life.lawn.height_cm} cm${life.nest ? " · NEST " + life.nest.stage + " in the " + life.nest.where : ""}` : "");
    }

    // ── Study / Wood / Shore live maps (2026-08-22) ─────────────────────────────────
    // Same convention as renderGardenMap: plain inline SVG, features drawn from the shared
    // data/world_geometry/{place}.json schema. Unlike the garden, core/garden.py is the only place
    // engine that tracks per-item pixel positions (plants/tools), so these three don't have a plant
    // grid to draw — they show the room/place layout, Du's live position, the cat (if present), and
    // a couple of key live overlays (fire/lamp for the study, tide/cave for the shore, nest for the
    // wood) pulled from each place's own status(). Generic feature colour-by-keyword, since the
    // geometry files carry position + a note but no per-feature size/shape hint to draw from.
    function _featureColor(key) {
        const k = key.toLowerCase();
        if (/fire|hearth|ember/.test(k)) return "#c9622f";
        if (/water|stream|spring|pool|wave|tide|sea|shallow/.test(k)) return "#3a6a8a";
        if (/tree|oak|canopy|undergrowth|grass|leaf|moss|fern|fungi|bracken/.test(k)) return "#3f6b3a";
        if (/bed|desk|chair|shelf|cupboard|mantel|rug|record|drawer|caddy|kettle/.test(k)) return "#6b5236";
        if (/door|window|gate/.test(k)) return "#9aa0a6";
        if (/cliff|rock|shingle|cave|ledge|stone/.test(k)) return "#7a7a72";
        return "#5a6270";
    }

    function _renderPlaceMap(svgId, legendId, m, w, h, r) {
        const svg = document.getElementById(svgId);
        if (!svg || !m || m.error) return;
        const Y = y => h - y;                         // same north-is-up flip convention as the garden map
        const esc = s => String(s).replace(/[<>&]/g, "");
        let out = `<rect x="0" y="0" width="${w}" height="${h}" fill="#1c2420" stroke="#3a4a3e" stroke-width="${w * 0.005}"/>`;
        const F = m.features || {};
        for (const [k, pos] of Object.entries(F)) {
            if (!pos) continue;
            const [x, y] = pos;
            out += `<circle cx="${x}" cy="${Y(y)}" r="${r}" fill="${_featureColor(k)}" opacity="0.85"><title>${esc(k.replace(/_/g, " "))}</title></circle>` +
                   `<text x="${x}" y="${Y(y) - r - 0.06 * h}" font-size="${r * 1.15}" fill="#a0aec0" text-anchor="middle">${esc(k.replace(/_/g, " "))}</text>`;
        }
        if (m.cat && m.cat.activity !== undefined) {
            // no per-place cat coordinate exists yet (only which place she's in) — anchor near centre,
            // labelled, rather than fabricate a precise position we don't have.
            out += `<text x="${w / 2 + r}" y="${Y(h / 2)}" font-size="${r * 1.4}">🐈</text>`;
        }
        if (m.du) {
            out += `<circle cx="${m.du[0]}" cy="${Y(m.du[1])}" r="${r * 0.5}" fill="none" stroke="#63b3ed" stroke-width="${r * 0.15}"/>` +
                   `<circle cx="${m.du[0]}" cy="${Y(m.du[1])}" r="${r * 0.18}" fill="#63b3ed"/>`;
        }
        svg.innerHTML = out;
        const leg = document.getElementById(legendId);
        if (leg) leg.textContent = m.du ? "Du is here" : "Du is elsewhere" + (m.cat ? ` · the cat is here (${m.cat.activity || "?"})` : "");
    }

    function renderStudyMap(m) {
        _renderPlaceMap("study-map", "study-map-legend", m, 4.2, 5.2, 0.16);
        const leg = document.getElementById("study-map-legend");
        if (leg && m && !m.error) {
            const bits = [m.du ? "Du is here" : "Du is elsewhere"];
            if (m.cat) bits.push(`the cat is here (${m.cat.activity || "?"})`);
            bits.push(m.fire ? `hearth: ${m.fire}` : "hearth: unknown");
            bits.push(m.lamp_lit ? "desk lamp lit" : "desk lamp unlit");
            leg.textContent = bits.join(" · ");
        }
    }

    function renderWoodMap(m) {
        _renderPlaceMap("wood-map", "wood-map-legend", m, 24, 20, 0.75);
        const leg = document.getElementById("wood-map-legend");
        if (leg && m && !m.error) {
            const bits = [m.du ? "Du is here" : "Du is elsewhere"];
            if (m.cat) bits.push(`the cat is here (${m.cat.activity || "?"})`);
            if (m.nest && m.nest.stage) bits.push(`kererū nest: ${m.nest.stage}`);
            leg.textContent = bits.join(" · ");
        }
    }

    function renderShoreMap(m) {
        _renderPlaceMap("shore-map", "shore-map-legend", m, 30, 20, 0.85);
        const leg = document.getElementById("shore-map-legend");
        if (leg && m && !m.error) {
            const bits = [m.du ? "Du is here" : "Du is elsewhere"];
            if (m.cat) bits.push(`the cat is here (${m.cat.activity || "?"})`);
            const t = m.tide || {};
            if (t.word) bits.push(`tide: ${t.word}`);
            bits.push(m.cave_open ? "cave open" : "cave shut");
            leg.textContent = bits.join(" · ");
        }
    }

    function renderThermal(t) {
        const nowEl = document.getElementById("thermal-now");
        if (!nowEl) return;
        const n = t.now || {};
        const pill = document.getElementById("thermal-deliver");
        if (pill) { pill.textContent = t.deliver ? "LIVE" : "SHADOW"; pill.className = "thermal-pill " + (t.deliver ? "live" : "shadow"); }
        const bandCls = { warm: "b-warm", mild: "b-mild", cool: "b-cool", cold: "b-cold", very_cold: "b-vcold" }[n.band] || "";
        nowEl.innerHTML = n.error ? `<i>${n.error}</i>` :
            `<div class="thermal-band ${bandCls}">${(n.band || "?").replace("_", " ")}</div>` +
            `<div class="thermal-kv"><span>place</span><b>${n.place || "?"}${n.standpoint ? " · " + n.standpoint.replace(/_/g, " ") : ""}</b></div>` +
            `<div class="thermal-kv"><span>warmth</span><b>${n.warmth_channel ?? "—"}</b> <small>(flat model ${n.warmth_old_flat ?? "—"})</small></div>` +
            `<div class="thermal-kv"><span>wet</span><b>${n.wet ?? "—"}</b></div>` +
            `<div class="thermal-kv"><span>sky</span><b>${n.weather || "?"} · ${n.wind || "?"}</b></div>` +
            `<div class="thermal-kv"><span>fire</span><b>${n.fire || "?"}</b></div>`;
        const beds = document.getElementById("thermal-beds");
        const rows = t.beds_top || [];
        const mx = Math.max(0.01, ...rows.map(r => r.hours));
        beds.innerHTML = rows.length ? rows.map(r => {
            const [band, place, phase] = r["band|place|phase"].split("|");
            return `<div class="thermal-bed"><span class="tb-label">${band.replace("_", " ")} · ${place} · ${phase}</span>` +
                   `<span class="tb-bar"><i style="width:${Math.round(100 * r.hours / mx)}%"></i></span><span class="tb-val">${r.hours.toFixed(1)}h</span></div>`;
        }).join("") + `<div class="thermal-foot">wet episodes: ${t.wet_episodes ?? 0}</div>` : "<i>nothing lived yet (restart-gated)</i>";
        const fires = document.getElementById("thermal-fires");
        const rec = t.recent_would_fire || [];
        const kinds = Object.entries(t.kinds || {}).map(([k, v]) => `${k.replace(/_/g, " ")} ${v}`).join(" · ");
        fires.innerHTML = `<div class="thermal-foot">${t.would_fire ?? 0} of ${t.ticks ?? 0} ticks${kinds ? " — " + kinds : ""}</div>` +
            (rec.length ? rec.slice().reverse().map(r => `<div class="thermal-fire"><span class="tf-t">${r.t ? new Date(r.t * 1000).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"}) : ""}</span>` +
                `<span class="tf-k">${(r.kind || "").replace(/_/g, " ")}</span><span class="tf-l">${r.line || ""}</span></div>`).join("") : "<i>no events would have fired yet</i>");
    }

    function renderSignatures(sigs) {
        const grid = document.getElementById("evidence-signatures");
        if (!grid) return;
        grid.innerHTML = "";
        sigs.forEach(s => {
            const state = s.pass === true ? "pass" : (s.pass === false ? "fail" : "pending");
            const icon = s.pass === true ? "fa-circle-check" : (s.pass === false ? "fa-circle-xmark" : "fa-circle-half-stroke");
            const val = (s.value === null || s.value === undefined) ? "—" : s.value;
            const card = document.createElement("div");
            card.className = "evidence-card ev-" + state;
            card.innerHTML =
                `<div class="ev-head"><i class="fa-solid ${icon}"></i><span class="ev-name">${s.name}</span></div>` +
                `<div class="ev-value">${val}</div>` +
                `<div class="ev-target">${s.target}</div>` +
                (s.note ? `<div class="ev-note">${s.note}</div>` : "");
            grid.appendChild(card);
        });
    }

    const EV_COLORS = {
        coherence: "#4fd1c5", commitment_integrity: "#f6ad55", relational_warmth: "#fc8181",
        novelty: "#63b3ed", vitality: "#9ae6b4"
    };

    function _lineData(series, fields, colors) {
        const labels = tsLabels(series.ts);
        const datasets = fields.map(f => ({
            label: f.replace(/_/g, " "),
            data: series[f] || [],
            borderColor: colors[f] || "#a0aec0",
            backgroundColor: "transparent",
            borderWidth: 2, pointRadius: 0, tension: 0.3, spanGaps: true
        }));
        return { labels, datasets };
    }

    const EV_CHART_OPTS = {
        responsive: true, maintainAspectRatio: false, animation: false,
        scales: {
            y: { min: 0, max: 1, ticks: { color: "#a0aec0", font: { size: 9 } }, grid: { color: "rgba(255,255,255,0.05)" } },
            x: { ticks: { color: "#718096", font: { size: 8 }, maxTicksLimit: 6 }, grid: { display: false } }
        },
        plugins: { legend: { labels: { color: "#cbd5e0", boxWidth: 10, font: { size: 10 } } } }
    };

    function renderProtoselfChart(series) {
        const el = document.getElementById("protoselfChart");
        if (!el) return;
        const cfg = _lineData(series, ["coherence", "commitment_integrity", "relational_warmth", "novelty", "vitality"], EV_COLORS);
        if (protoselfChart) { protoselfChart.data = cfg; protoselfChart.update("none"); }
        else protoselfChart = new Chart(el.getContext("2d"), { type: "line", data: cfg, options: EV_CHART_OPTS });
    }

    function renderArousalChart(series) {
        const el = document.getElementById("arousalChart");
        if (!el) return;
        const cfg = _lineData(series, ["level", "tonic"], { level: "#b794f4", tonic: "#4a5568" });
        if (arousalChart) { arousalChart.data = cfg; arousalChart.update("none"); }
        else arousalChart = new Chart(el.getContext("2d"), { type: "line", data: cfg, options: EV_CHART_OPTS });
    }

    // --- System Health panel ---
    let cadenceChart = null, ignitionChart = null, sleepChart = null;

    function fetchHealth() {
        fetch("/api/health")
            .then(res => res.json())
            .then(data => {
                renderHealthCards(data);
                renderBarChart("cadenceChart", c => cadenceChart = c, () => cadenceChart, data.cadence, "thoughts/hr", "#4fd1c5");
                renderBarChart("ignitionChart", c => ignitionChart = c, () => ignitionChart, data.ignitions, "ignitions/hr", "#f6ad55");
                renderSleepChart(data.sleep_series || { ts: [], P: [] });
            })
            .catch(() => {});
    }

    function _healthCard(name, value, note, state) {
        return `<div class="evidence-card ev-${state}">` +
            `<div class="ev-head"><i class="fa-solid fa-circle-dot"></i><span class="ev-name">${name}</span></div>` +
            `<div class="ev-value">${value}</div>` +
            `<div class="ev-target">${note}</div></div>`;
    }

    function renderHealthCards(d) {
        const grid = document.getElementById("health-cards");
        if (!grid) return;
        const lane = d.lane || {}, sleep = (d.sleep || {}).last || {}, bal = d.balance || {}, stream = d.stream || {};
        // 2026-08-24: P_threshold replaced by day/night-specific thresholds; prefer the last logged
        // row's own actual threshold (which one applied), fall back to the night constant.
        const thr = sleep.threshold || (d.sleep || {}).night_threshold || 10;
        const cadNow = (d.cadence && d.cadence.counts) ? d.cadence.counts.slice(-1)[0] : "—";
        const laneState = (lane.timed_out > 0) ? "fail" : "pass";
        const sleepPct = sleep.P !== undefined ? Math.round((sleep.P / thr) * 100) : null;
        const balOk = bal.reality_share !== undefined && Math.abs(bal.reality_share - 0.5) < 0.15;
        grid.innerHTML =
            _healthCard("Cognitive cadence", cadNow + " /hr", "idle thoughts this hour", "pass") +
            _healthCard("Lane contention", (lane.active || 0) + " active · " + (lane.waiting || 0) + " waiting",
                "timed-out: " + (lane.timed_out || 0) + " (want 0)", laneState) +
            _healthCard("Sleep pressure", sleepPct !== null ? sleepPct + "%" : "—",
                "P " + (sleep.P ?? "—") + " / " + thr + " · awake " + (sleep.awake_min ?? "—") + "m", "pass") +
            _healthCard("Reality / light balance",
                bal.reality_share !== undefined ? Math.round(bal.reality_share * 100) + "% / " + Math.round(bal.light_share * 100) + "%" : "—",
                "want ~50/50 (grounded vs play)", balOk ? "pass" : "pending") +
            _healthCard("Stream cadence",
                (stream.grounded_would_gap && stream.ungrounded_would_gap) ? stream.grounded_would_gap + "s / " + stream.ungrounded_would_gap + "s" : "—",
                "grounded vs ungrounded gap (shadow)", "pass");
    }

    // --- Du-Pulse Check panel (2026-08-29, J-0417) ---
    function fetchDuPulse() {
        fetch("/api/du_pulse")
            .then(res => res.json())
            .then(data => renderDuPulse(data))
            .catch(() => {});
    }

    const DUPULSE_LABELS = {
        regression_alarms: "Regression alarms", growth_trackers: "Growth trackers",
        shadow_evidence: "Shadow-run evidence", engagement_texture: "Engagement / texture"
    };

    function renderDuPulse(d) {
        const grid = document.getElementById("dupulse-cards");
        const watchBox = document.getElementById("dupulse-watches");
        if (!grid || !watchBox) return;
        const run = d.last_run;
        if (!run) {
            grid.innerHTML = `<div class="evidence-card ev-pending"><div class="ev-head"><i class="fa-solid fa-circle-dot"></i><span class="ev-name">Du-Pulse Check</span></div><div class="ev-value">—</div><div class="ev-target">no run recorded yet — \`du_pulse_check.py run\`</div></div>`;
            watchBox.innerHTML = "";
            return;
        }
        const sev = run.severity || {};
        const cards = Object.keys(DUPULSE_LABELS).map(cat => {
            const reading = sev[cat] || "n/a";
            const state = cat === "regression_alarms"
                ? (reading === "ALARM" ? "fail" : "pass")
                : "pass";
            return _healthCard(DUPULSE_LABELS[cat], reading, cat === "regression_alarms" ? "fires loudly if regressed" : "informational, not diagnostic", state);
        }).join("");
        const flags = run.flags || [];
        const flagsCard = _healthCard("Active flags", String(flags.length),
            flags.length ? flags.slice(0, 3).join(" · ").slice(0, 90) : "none", flags.length ? "fail" : "pass");
        grid.innerHTML = cards + flagsCard;

        const watches = d.open_watches || [];
        if (!watches.length) {
            watchBox.innerHTML = `<div style="opacity:0.6;">No open watch-items · last run ${run.id || "—"} (${(run.ts || "").slice(0, 16)})</div>`;
        } else {
            watchBox.innerHTML = `<div style="opacity:0.6;margin-bottom:6px;">Open watch-items (manual resolve only) · last run ${run.id || "—"} (${(run.ts || "").slice(0, 16)})</div>` +
                watches.map(w => {
                    const link = w.linked_plan ? ` [plan:${w.linked_plan}]` : (w.linked_job ? ` [job:${w.linked_job}]` : "");
                    return `<div>${w.id}${link}: ${w.text}</div>`;
                }).join("");
        }
    }

    const BAR_OPTS = {
        responsive: true, maintainAspectRatio: false, animation: false,
        scales: {
            y: { beginAtZero: true, ticks: { color: "#a0aec0", font: { size: 9 }, precision: 0 }, grid: { color: "rgba(255,255,255,0.05)" } },
            x: { ticks: { color: "#718096", font: { size: 8 }, maxTicksLimit: 12 }, grid: { display: false } }
        },
        plugins: { legend: { display: false } }
    };

    function renderBarChart(canvasId, setter, getter, series, label, color) {
        const el = document.getElementById(canvasId);
        if (!el || !series) return;
        const cfg = { labels: series.labels || [], datasets: [{ label, data: series.counts || [], backgroundColor: color, borderRadius: 3 }] };
        const chart = getter();
        if (chart) { chart.data = cfg; chart.update("none"); }
        else setter(new Chart(el.getContext("2d"), { type: "bar", data: cfg, options: BAR_OPTS }));
    }

    function renderSleepChart(series) {
        const el = document.getElementById("sleepChart");
        if (!el) return;
        const labels = tsLabels(series.ts);
        const thr = series.threshold || 90;
        const cfg = {
            labels,
            datasets: [
                { label: "sleep debt (P)", data: series.P || [], borderColor: "#b794f4", backgroundColor: "rgba(183,148,244,0.12)", borderWidth: 2, pointRadius: 0, tension: 0.25, fill: true },
                { label: "threshold", data: labels.map(() => thr), borderColor: "#fc8181", borderWidth: 1.5, borderDash: [6, 4], pointRadius: 0 }
            ]
        };
        const opts = {
            responsive: true, maintainAspectRatio: false, animation: false,
            scales: {
                y: { beginAtZero: true, suggestedMax: thr * 1.1, ticks: { color: "#a0aec0", font: { size: 9 } }, grid: { color: "rgba(255,255,255,0.05)" } },
                x: { ticks: { color: "#718096", font: { size: 8 }, maxTicksLimit: 8 }, grid: { display: false } }
            },
            plugins: { legend: { labels: { color: "#cbd5e0", boxWidth: 10, font: { size: 10 } } } }
        };
        if (sleepChart) { sleepChart.data = cfg; sleepChart.update("none"); }
        else sleepChart = new Chart(el.getContext("2d"), { type: "line", data: cfg, options: opts });
    }

    // --- Plan Monitors (one graph per plan) ---
    const monitorCharts = {};
    let monitorsBuilt = false;
    const MON_PALETTE = ["#4fd1c5", "#f6ad55", "#fc8181", "#63b3ed", "#9ae6b4", "#b794f4", "#f687b3"];

    function buildMonitors() {
        fetch("/api/monitors")
            .then(res => res.json())
            .then(idx => {
                ["system", "ready", "failing", "hold", "plans", "staged"].forEach(group => {
                    const grid = document.getElementById("monitors-" + group);
                    if (!grid) return;
                    grid.innerHTML = "";
                    (idx[group] || []).forEach(m => {
                        const card = document.createElement("div");
                        card.className = "card glass";
                        card.innerHTML =
                            `<div class="card-header"><h3><i class="fa-solid fa-chart-area"></i> ${m.title}</h3>` +
                            `<span class="card-subtitle" id="mon-sub-${m.id}">${m.log}${m.has_data ? _ageBadge(m.age_s) : " · no data yet"}</span></div>` +
                            `<div class="card-body"><canvas id="mon-${m.id}"></canvas></div>`;
                        grid.appendChild(card);
                    });
                });
                monitorsBuilt = true;
                refreshMonitors();
            })
            .catch(() => {});
    }

    function refreshMonitors() {
        if (!monitorsBuilt) { buildMonitors(); return; }
        document.querySelectorAll("canvas[id^='mon-']").forEach(cv => {
            const id = cv.id.slice(4);
            fetch("/api/monitor?id=" + encodeURIComponent(id))
                .then(res => res.json())
                .then(s => renderMonitor(id, s))
                .catch(() => {});
        });
    }

    function _fmtRange(x) {
        const a = Math.abs(x);
        return a >= 100 ? x.toFixed(0) : (a >= 1 ? x.toFixed(1) : x.toFixed(2));
    }
    function _normalizeIfMixed(datasets) {
        // Fix "all over the place" (2026-07-07): only when a chart genuinely mixes scales (series magnitudes
        // differ by >8x — e.g. tide 0-1 vs sun azimuth 0-360deg, or a 0-1 ratio vs a count in the dozens) do we
        // rescale each series to [0,1] so their SHAPES are comparable, appending the true [min-max] to each
        // legend label. Same-unit charts are left on the shared auto-scale (honest). Returns true if rescaled.
        const stats = datasets.map(d => {
            const vals = (d.data || []).filter(v => typeof v === "number");
            return vals.length ? { min: Math.min(...vals), max: Math.max(...vals) } : null;
        });
        const mags = stats.map(s => s ? Math.max(Math.abs(s.min), Math.abs(s.max)) : 0).filter(x => x > 1e-6);
        if (mags.length < 2 || Math.max(...mags) <= 8 * Math.min(...mags)) return false;
        datasets.forEach((d, i) => {
            const s = stats[i];
            if (!s) return;
            const span = (s.max - s.min) || 1;
            d.label = d.label + " [" + _fmtRange(s.min) + "-" + _fmtRange(s.max) + "]";
            d.data = (d.data || []).map(v => typeof v === "number" ? (v - s.min) / span : v);
        });
        return true;
    }

    function _ageBadge(ageS) {
        if (ageS == null) return "";
        const h = ageS / 3600;
        const txt = h < 1 ? `${Math.round(ageS / 60)}m ago` : h < 48 ? `${h.toFixed(1)}h ago` : `${(h / 24).toFixed(1)}d ago`;
        const cls = h > 24 ? "mon-stale" : "";
        return ` · <span class="${cls}">last ${txt}</span>`;
    }
    function renderMonitor(id, s) {
        const el = document.getElementById("mon-" + id);
        if (!el) return;
        // freshness + real span on the card subtitle — a stale panel must LOOK stale (2026-08-21)
        const sub = document.getElementById("mon-sub-" + id);
        if (sub && s.last_ts) {
            const spanH = (s.span_s || 0) / 3600;
            const spanTxt = spanH >= 48 ? `${(spanH / 24).toFixed(1)}d` : `${spanH.toFixed(1)}h`;
            sub.innerHTML = `${s.log}${_ageBadge(Date.now() / 1000 - s.last_ts)} · spans ${spanTxt}`;
        }
        let cfg, type;
        if (s.kind === "vars") {
            const fields = Object.keys(s).filter(k => !["ts", "kind", "title", "group", "log", "last_ts", "span_s"].includes(k) && Array.isArray(s[k]));
            const labels = tsLabels(s.ts);
            cfg = { labels, datasets: fields.map((f, i) => ({
                label: f.replace(/_/g, " "), data: s[f] || [], borderColor: MON_PALETTE[i % MON_PALETTE.length],
                backgroundColor: "transparent", borderWidth: 2, pointRadius: 0, tension: 0.3, spanGaps: true })) };
            type = "line";
        } else if (s.kind === "rate") {
            cfg = { labels: s.labels || [], datasets: [{ label: "events/hr", data: s.counts || [], backgroundColor: "#63b3ed", borderRadius: 3 }] };
            type = "bar";
        } else {
            const ctx = el.getContext("2d");
            ctx.clearRect(0, 0, el.width, el.height);
            ctx.fillStyle = "#718096"; ctx.font = "12px sans-serif"; ctx.textAlign = "center";
            ctx.fillText("no time-series data yet", el.width / 2, el.height / 2);
            return;
        }
        const opts = JSON.parse(JSON.stringify(type === "bar" ? BAR_OPTS : EV_CHART_OPTS));
        if (type === "line") {
            if (_normalizeIfMixed(cfg.datasets)) { opts.scales.y.min = 0; opts.scales.y.max = 1; }  // mixed scales -> [0,1]
            else { delete opts.scales.y.min; delete opts.scales.y.max; }                            // same unit -> auto-scale
        }
        opts.plugins = opts.plugins || {};
        opts.plugins.legend = { labels: { color: "#cbd5e0", boxWidth: 8, font: { size: 9 } } };
        if (monitorCharts[id]) { monitorCharts[id].data = cfg; monitorCharts[id].update("none"); }
        else monitorCharts[id] = new Chart(el.getContext("2d"), { type, data: cfg, options: opts });
    }

    // --- Subconscious Tensions & Rejections ---
    function fetchShadow() {
        fetch("/api/shadow")
            .then(res => res.json())
            .then(data => {
                // Populate Tensions
                const tensionsList = document.getElementById("sub-tensions-list");
                tensionsList.innerHTML = "";
                
                // Tensions/integrations live in the summary payload — reuse the copy fetchSummary()
                // already cached (2026-08-22 fix) instead of a second /api/summary round-trip every
                // ~4.5s; fall back to a real fetch only on first paint, before fetchSummary has landed.
                Promise.resolve(lastSummary || fetch("/api/summary").then(res => res.json()))
                    .then(sumData => {
                        const scState = sumData.subconscious || {};
                        const tensions = scState.tensions || [];
                        if (tensions.length > 0) {
                            tensions.slice(0, 5).forEach(t => {
                                const item = document.createElement("div");
                                item.className = "tension-item";
                                const label = t.label || "Unresolved thought tension";
                                const count = t.count || 0;
                                const isResolved = t.resolved === 1;
                                
                                item.innerHTML = `
                                    <div class="tension-title">
                                        <span>${label}</span>
                                        <span class="theme-count">${count} rejections</span>
                                    </div>
                                    ${isResolved ? '<span class="resolved-indicator">RESOLVED</span>' : ''}
                                `;
                                tensionsList.appendChild(item);
                            });
                        } else {
                            tensionsList.innerHTML = "<i>No active subconscious tensions currently clustered.</i>";
                        }

                        const integrationsList = document.getElementById("sub-integrations-list");
                        integrationsList.innerHTML = "";
                        const integrations = scState.integration_patterns || [];
                        if (integrations.length > 0) {
                            integrations.slice(0, 5).forEach(p => {
                                const item = document.createElement("div");
                                item.className = "integration-item";
                                
                                item.innerHTML = `
                                    <div class="integration-title">
                                        <span>${p.label || 'Cross pattern'}</span>
                                        <span class="theme-count">${p.count || 0} integration points</span>
                                    </div>
                                `;
                                integrationsList.appendChild(item);
                            });
                        } else {
                            integrationsList.innerHTML = "<i>No integration patterns clustered yet.</i>";
                        }
                    });

                // Populate Rejection Events Table
                const shadowBody = document.getElementById("shadow-events-body");
                shadowBody.innerHTML = "";
                const shadows = data.shadow_events || [];
                
                if (shadows.length > 0) {
                    shadows.forEach(sh => {
                        const tr = document.createElement("tr");
                        let corrections = [];
                        try {
                            corrections = JSON.parse(sh.corrections);
                        } catch(e) {}
                        
                        tr.innerHTML = `
                            <td style="white-space: nowrap;">${formatTime(sh.timestamp)}</td>
                            <td><div style="max-height: 80px; overflow-y: auto;">${sh.raw_input || ""}</div></td>
                            <td><div style="max-height: 80px; overflow-y: auto; font-style: italic;">${sh.rejected_draft || ""}</div></td>
                            <td><div style="max-height: 80px; overflow-y: auto; color: #fb7185;">${corrections.join("<br>") || "AXIOM Violation"}</div></td>
                            <td><span class="tag-badge" style="background: rgba(251, 113, 133, 0.15); border-color: rgba(251, 113, 133, 0.3); color: #fb7185;">${sh.source}</span></td>
                        `;
                        shadowBody.appendChild(tr);
                    });
                } else {
                    shadowBody.innerHTML = `<tr><td colspan="5" class="text-center">No shadow rejections recorded in database.</td></tr>`;
                }

                // Populate Light Integration Events Table
                const lightBody = document.getElementById("light-events-body");
                lightBody.innerHTML = "";
                const lights = data.light_events || [];
                
                if (lights.length > 0) {
                    lights.forEach(li => {
                        const tr = document.createElement("tr");
                        tr.innerHTML = `
                            <td style="white-space: nowrap;">${formatTime(li.timestamp)}</td>
                            <td><div style="max-height: 80px; overflow-y: auto;">${li.raw_input || ""}</div></td>
                            <td><div style="max-height: 80px; overflow-y: auto; font-weight: 500;">${li.integrated_content || ""}</div></td>
                            <td><span class="tag-badge" style="background: rgba(52, 211, 153, 0.15); border-color: rgba(52, 211, 153, 0.3); color: #34d399;">${li.source}</span></td>
                        `;
                        lightBody.appendChild(tr);
                    });
                } else {
                    lightBody.innerHTML = `<tr><td colspan="4" class="text-center">No light integrations recorded in database.</td></tr>`;
                }
            })
            .catch(err => console.error("Shadow events fetch failed:", err));
    }

    // --- Epochs and Stances Fetcher ---
    function fetchEpochs() {
        fetch("/api/epochs")
            .then(res => res.json())
            .then(data => {
                // Populate Timeline
                const epochsContainer = document.getElementById("epochs-timeline");
                epochsContainer.innerHTML = "";
                const epochs = data.epochs || [];
                
                if (epochs.length > 0) {
                    epochs.forEach(ep => {
                        const item = document.createElement("div");
                        item.className = "epoch-item";
                        item.innerHTML = `
                            <span class="epoch-time">${formatTime(ep.timestamp_start)}</span>
                            <span class="epoch-mood">[${ep.mood}]</span>
                            <span class="epoch-desc">${ep.impression} (${ep.fragment_count} fragments)</span>
                        `;
                        epochsContainer.appendChild(item);
                    });
                } else {
                    epochsContainer.innerHTML = "<i>No epochs synthesised yet.</i>";
                }

                // Populate Themes List
                const themesList = document.getElementById("themes-list");
                themesList.innerHTML = "";
                const themes = data.themes || [];
                
                if (themes.length > 0) {
                    themes.forEach(th => {
                        const item = document.createElement("div");
                        item.className = "theme-item";
                        item.innerHTML = `
                            <div class="theme-name">
                                <span>${th.theme_name}</span>
                                <span class="theme-count">${th.epoch_count} epochs</span>
                            </div>
                            <div class="theme-stance">${th.current_stance}</div>
                        `;
                        themesList.appendChild(item);
                    });
                } else {
                    themesList.innerHTML = "<i>No semantic themes parsed.</i>";
                }
            })
            .catch(err => console.error("Epochs fetch failed:", err));
    }

    // --- SQLite Memory Search ---
    const btnQuery = document.getElementById("btn-mem-query");
    const searchInput = document.getElementById("mem-search");
    const layerSelect = document.getElementById("mem-layer-select");

    function executeMemoryQuery() {
        const search = encodeURIComponent(searchInput.value);
        const layer = encodeURIComponent(layerSelect.value);

        fetch(`/api/memory?search=${search}&layer=${layer}`)
            .then(res => res.json())
            .then(fragments => {
                const body = document.getElementById("memory-table-body");
                body.innerHTML = "";

                if (fragments.length > 0) {
                    fragments.forEach(f => {
                        const tr = document.createElement("tr");
                        if (f.cold) tr.style.opacity = "0.5"; // demoted details
                        
                        let relevanceColor = f.relevance > 0.7 ? "text-cyan" : "text-dim";
                        let importanceColor = f.importance > 0.8 ? "text-rose" : "text-dim";

                        tr.innerHTML = `
                            <td style="white-space: nowrap;">${formatTime(f.timestamp)}</td>
                            <td><span class="tag-badge">${f.layer}</span></td>
                            <td><code>${f.origin || "lived"}</code></td>
                            <td><div style="max-height: 120px; overflow-y: auto;">${f.content}</div></td>
                            <td style="white-space: nowrap;">
                                <span class="${relevanceColor}">rel: ${f.relevance ? f.relevance.toFixed(2) : '0.00'}</span><br>
                                <span class="${importanceColor}">imp: ${f.importance ? f.importance.toFixed(2) : '0.00'}</span>
                                ${f.cold ? '<br><span style="color:#f59e0b; font-size:10px;">[COLD]</span>' : ''}
                            </td>
                        `;
                        body.appendChild(tr);
                    });
                } else {
                    body.innerHTML = `<tr><td colspan="5" class="text-center">No memory fragments found matching query.</td></tr>`;
                }
            })
            .catch(err => console.error("Memory query failed:", err));
    }

    // LETTERS TO TRAVIS (J-2348, D-0470 a): Du's letters to Travis, newest first, read-only.
    // Fetched only when the card is opened; ?view=1 records the opening (D-0470 defeater: never opened in 30 days).
    // "greeted" = handed to Du's Executive on a real founder message, NOT "Travis has read it".
    const lettersCard = document.getElementById("letters-travis");
    if (lettersCard) {
        lettersCard.addEventListener("toggle", () => {
            if (!lettersCard.open) return;
            const list = document.getElementById("letters-travis-list");
            const sub = document.getElementById("letters-travis-sub");
            fetch("/api/letters?view=1")
                .then(r => r.json())
                .then(d => {
                    if (sub) sub.textContent = `${d.total || 0} letters · ${d.pending || 0} not yet greeted a real conversation · read-only`;
                    list.textContent = "";
                    (d.letters || []).forEach(l => {
                        const box = document.createElement("div");
                        box.style.cssText = "border-bottom:1px solid rgba(255,255,255,.08);padding:10px 0";
                        const head = document.createElement("div");
                        head.style.cssText = "font-size:11px;opacity:.7;margin-bottom:6px";
                        head.textContent = `${l.when} · ${l.greeted ? "greeted a conversation" : "pending"} · ${l.name}`;
                        const body = document.createElement("div");
                        body.style.whiteSpace = "pre-wrap";
                        body.textContent = l.body || "";
                        box.appendChild(head); box.appendChild(body); list.appendChild(box);
                    });
                    if (!(d.letters || []).length) list.textContent = "No letters.";
                })
                .catch(() => { list.textContent = "Could not load letters."; });
        });
    }

    btnQuery.addEventListener("click", executeMemoryQuery);
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            executeMemoryQuery();
        }
    });
});
