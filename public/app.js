// SENTINEL × PEGASUS — Dashboard Frontend Logic
document.addEventListener("DOMContentLoaded", () => {
    initSentinelApp();
});

let currentProjectId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
let currentEvidenceIds = [];
let investigationRunning = false;

async function initSentinelApp() {
    setupEventListeners();
    initConstellationCanvas();
    initSidebarNav();
    initClock();
    await loadProjectData(currentProjectId);
}

function setupEventListeners() {
    const select = document.getElementById("project-select");
    if (select) {
        select.addEventListener("change", async (e) => {
            currentProjectId = e.target.value;
            await loadProjectData(currentProjectId);
        });
    }

    const btnInvestigate = document.getElementById("btn-trigger-investigation");
    if (btnInvestigate) {
        btnInvestigate.addEventListener("click", async () => {
            await runInvestigationFlow();
        });
    }

    const btnCorrection = document.getElementById("btn-submit-correction");
    if (btnCorrection) {
        btnCorrection.addEventListener("click", async () => {
            await submitAuditorCorrection();
        });
    }
}

function initSidebarNav() {
    const sectionMap = {
        'Dashboard': '.fin-strip',
        'Projects': '.fin-project-card',
        'Investigations': '.card-trace',
        'Evidence Hub': '.card-evidence',
        'Evidence Graph': '.card-constellation',
        'Case Memory': '.card-summary',
        'Reports': '.card-progress',
        'Settings': '.app-header',
    };

    document.querySelectorAll(".nav-item").forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            const label = item.querySelector("span");
            if (!label) return;
            const target = sectionMap[label.textContent.trim()];
            if (target) {
                const el = document.querySelector(target);
                if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
}

// ========== CONSTELLATION CANVAS ==========
function initConstellationCanvas() {
    const canvas = document.getElementById("constellation-canvas");
    const viewport = document.getElementById("constellation-viewport");
    if (!canvas || !viewport) return;

    const ctx = canvas.getContext("2d");
    let stars = [];
    let frame = 0;

    const nodes = [
        { id: "cnode-e1", x: 0.08, y: 0.18, color: "#34D399" },
        { id: "cnode-e4", x: 0.35, y: 0.08, color: "#F87171" },
        { id: "cnode-e3", x: 0.66, y: 0.14, color: "#60A5FA" },
        { id: "cnode-e2", x: 0.12, y: 0.60, color: "#34D399" },
        { id: "cnode-e5", x: 0.42, y: 0.52, color: "#FBBF24" },
        { id: "cnode-e6", x: 0.68, y: 0.56, color: "#FBBF24" },
    ];

    const connections = [
        [0, 1], [1, 2], [0, 3], [3, 4], [4, 5], [2, 5], [1, 4], [0, 4],
    ];

    function resize() {
        const rect = viewport.getBoundingClientRect();
        canvas.width = rect.width;
        canvas.height = rect.height;
        createStars();
    }

    function createStars() {
        stars = [];
        for (let i = 0; i < 80; i++) {
            stars.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: Math.random() * 1.2 + 0.3,
                alpha: Math.random() * 0.4 + 0.1,
                speed: Math.random() * 0.006 + 0.002,
                phase: Math.random() * Math.PI * 2,
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        frame++;

        // Background nebula
        const grd = ctx.createRadialGradient(
            canvas.width * 0.4, canvas.height * 0.3, 20,
            canvas.width * 0.4, canvas.height * 0.3, canvas.width * 0.5
        );
        grd.addColorStop(0, "rgba(124,143,255,0.04)");
        grd.addColorStop(0.5, "rgba(139,92,246,0.02)");
        grd.addColorStop(1, "transparent");
        ctx.fillStyle = grd;
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Stars
        for (const s of stars) {
            const t = Math.sin(frame * s.speed + s.phase) * 0.4 + 0.6;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(200,210,255,${s.alpha * t})`;
            ctx.fill();
        }

        // Connections
        for (const [i, j] of connections) {
            const a = nodes[i];
            const b = nodes[j];
            const ax = a.x * canvas.width + 40;
            const ay = a.y * canvas.height + 10;
            const bx = b.x * canvas.width + 40;
            const by = b.y * canvas.height + 10;

            const pulse = Math.sin(frame * 0.02 + i * 0.5) * 0.3 + 0.5;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(bx, by);
            ctx.strokeStyle = `rgba(124,143,255,${0.08 * pulse})`;
            ctx.lineWidth = 1;
            ctx.stroke();

            // Midpoint glow
            const mx = (ax + bx) / 2;
            const my = (ay + by) / 2;
            const mg = ctx.createRadialGradient(mx, my, 0, mx, my, 12);
            mg.addColorStop(0, `rgba(124,143,255,${0.06 * pulse})`);
            mg.addColorStop(1, "transparent");
            ctx.fillStyle = mg;
            ctx.fillRect(mx - 12, my - 12, 24, 24);
        }

        // Node glows
        for (const n of nodes) {
            const nx = n.x * canvas.width + 40;
            const ny = n.y * canvas.height + 10;
            const glow = ctx.createRadialGradient(nx, ny, 0, nx, ny, 30);
            glow.addColorStop(0, hexToRgba(n.color, 0.15));
            glow.addColorStop(1, "transparent");
            ctx.fillStyle = glow;
            ctx.beginPath();
            ctx.arc(nx, ny, 30, 0, Math.PI * 2);
            ctx.fill();
        }

        requestAnimationFrame(draw);
    }

    resize();
    draw();
    window.addEventListener("resize", resize);
}

// ========== DATA LOADING ==========
async function loadProjectData(projectId) {
    try {
        await loadProjectInfo(projectId);
        await loadMoneyTrail(projectId);
        await loadEvidenceGraph(projectId);
        await loadInvestigationStatus(projectId);
    } catch (err) {
        console.error("Failed to load Sentinel data:", err);
    }
}

// ========== INVESTIGATION FLOW ==========
async function runInvestigationFlow() {
    if (investigationRunning) return;
    investigationRunning = true;

    const btn = document.getElementById("btn-trigger-investigation");
    const origText = btn ? btn.innerHTML : "";
    const traceLog = document.getElementById("trace-log");
    const traceStatus = document.getElementById("trace-status-text");

    try {
        if (btn) { btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> INITIALIZING...'; btn.disabled = true; }

        const smSection = document.getElementById("state-machine-section");
        if (smSection) {
            smSection.style.display = "";
            smSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        updateStateMachine("step-discover");
        if (traceStatus) traceStatus.innerText = "Agent initializing...";
        await sleep(400);

        updateStateMachine("step-investigate");
        if (traceStatus) traceStatus.innerText = "Running investigation loop...";
        await sleep(300);

        updateStateMachine("step-analyzing");
        const res = await fetch("/api/agent-investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_id: currentProjectId })
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const agentResult = await res.json();

        if (agentResult.trace && agentResult.trace.length > 0) {
            for (let i = 0; i < agentResult.trace.length; i++) {
                const step = agentResult.trace[i];
                await sleep(250);
                appendTraceStep(step.step_type, step.description, step.data);

                if (step.step_type === "tool_call" && step.data.tool === "analyze_photo" && step.data.result) {
                    updateVisionPanel(step.data.result);
                }
                if (step.step_type === "deliver") {
                    updateStateMachine("step-review");
                }
            }
        }

        const iterations = agentResult.iterations || 0;
        const toolCalls = (agentResult.trace || []).filter(s => s.step_type === "tool_call").length;
        const iterEl = document.getElementById("trace-iteration-count");
        const toolEl = document.getElementById("trace-tool-count");
        if (iterEl) iterEl.innerText = `${iterations} iteration${iterations !== 1 ? 's' : ''}`;
        if (toolEl) toolEl.innerText = `${toolCalls} tool call${toolCalls !== 1 ? 's' : ''}`;

        const finalState = agentResult.final_state || "UNKNOWN";
        if (traceStatus) traceStatus.innerText = `Agent complete — ${finalState.replace(/_/g, ' ')}`;

        updateStarProgress(finalState);
        showSuccess(`Investigation complete: ${finalState.replace(/_/g, ' ')}. ${agentResult.contradiction_count || 0} discrepancies found.`);

        try {
            await fetch("/api/investigate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_id: currentProjectId })
            });
        } catch {}

        await loadProjectInfo(currentProjectId);
        await loadMoneyTrail(currentProjectId);
        await loadEvidenceGraph(currentProjectId);
        await loadInvestigationStatus(currentProjectId);

    } catch (err) {
        console.error("Investigation failed:", err);
        if (traceStatus) traceStatus.innerText = "Agent error";
        showError("Investigation failed. Please try again.");
    } finally {
        if (btn) { btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run AI Investigation'; btn.disabled = false; }
        investigationRunning = false;
    }
}

function updateStarProgress(state) {
    const stars = document.querySelectorAll("#star-progress .ss");
    if (!stars.length) return;

    let activeIdx = 2;
    if (state.includes("COLLECT")) activeIdx = 0;
    else if (state.includes("VERIF")) activeIdx = 1;
    else if (state.includes("CONTRADICT") || state.includes("ANALYZ")) activeIdx = 2;
    else if (state.includes("SYNTH") || state.includes("FINDING")) activeIdx = 3;
    else if (state.includes("REVIEW") || state.includes("COMPLETE")) activeIdx = 4;

    stars.forEach((s, i) => {
        s.classList.remove("completed", "active", "pending");
        if (i < activeIdx) s.classList.add("completed");
        else if (i === activeIdx) s.classList.add("active");
        else s.classList.add("pending");
    });
}

async function submitAuditorCorrection() {
    const interpEl = document.getElementById("corr-interp");
    const reasonEl = document.getElementById("corr-reason");
    const interp = interpEl ? interpEl.value : "";
    const reason = reasonEl ? reasonEl.value : "";
    const btn = document.getElementById("btn-submit-correction");
    if (!btn) return;
    const origText = btn.innerText;

    try {
        btn.innerText = "STORING CORRECTION...";
        btn.disabled = true;
        updateStateMachine("step-correction");

        const res = await fetch("/api/human-correction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                project_id: currentProjectId,
                investigation_id: "inv_demo_phase5",
                corrected_interpretation: interp,
                reason_for_correction: reason,
                evidence_ids: currentEvidenceIds.length > 0 ? currentEvidenceIds : ["e1-mb", "e2-photo"]
            })
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        await res.json();

        const successMsg = document.getElementById("correction-success-msg");
        if (successMsg) {
            successMsg.style.display = "block";
            setTimeout(() => { successMsg.style.display = "none"; }, 5000);
        }

        updateStateMachine("step-memory");
        showSuccess("Auditor correction stored. Case memory precedent created!");
        await sleep(800);
        await loadInvestigationStatus(currentProjectId);
    } catch (err) {
        console.error("Correction failed:", err);
        showError("Correction submission failed.");
    } finally {
        btn.innerText = origText;
        btn.disabled = false;
    }
}

// ========== STATE MACHINE ==========
function updateStateMachine(activeStepId) {
    const steps = ["step-discover", "step-investigate", "step-analyzing", "step-graph", "step-conflict", "step-review", "step-correction", "step-memory", "step-second-case"];
    const activeIdx = steps.indexOf(activeStepId);
    steps.forEach((id, idx) => {
        const el = document.getElementById(id);
        if (el) {
            el.classList.remove("active", "completed");
            if (id === activeStepId) el.classList.add("active");
            else if (activeIdx >= 0 && idx < activeIdx) el.classList.add("completed");
        }
    });
}

// ========== NOTIFICATIONS ==========
function showError(msg) { showToast(msg, "#DC2626", "rgba(220,38,38,0.15)"); }
function showSuccess(msg) { showToast(msg, "#10B981", "rgba(16,185,129,0.15)"); }

function showToast(msg, borderColor, bgColor) {
    const existing = document.querySelector(".sentinel-toast");
    if (existing) existing.remove();
    const toast = document.createElement("div");
    toast.className = "sentinel-toast";
    toast.style.cssText = `position:fixed;top:20px;right:20px;background:${bgColor};backdrop-filter:blur(12px);color:#FFF;padding:14px 24px;border-radius:12px;font-weight:600;z-index:9999;border:1px solid ${borderColor};box-shadow:0 8px 30px rgba(0,0,0,0.4);font-size:14px;max-width:400px;animation:slideIn 0.3s ease;`;
    toast.innerText = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-10px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ========== CLOCK ==========
function initClock() {
    const timeEl = document.getElementById("clock-time");
    const dateEl = document.getElementById("clock-date");
    if (!timeEl || !dateEl) return;

    function tick() {
        const now = new Date();
        timeEl.textContent = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", hour12: false });
        dateEl.textContent = now.toLocaleDateString("en-IN", { weekday: "short", day: "2-digit", month: "short", year: "numeric" });
    }

    tick();
    setInterval(tick, 10000);
}

// ========== UTILITIES ==========
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
}

function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

function formatINR(val) {
    if (val === null || val === undefined) return "₹0";
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);
}

function animateCounters() {
    document.querySelectorAll(".fin-amt, .risk-num").forEach(el => {
        const text = el.innerText;
        const match = text.match(/[\d,]+/);
        if (match && !el.dataset.animated) {
            const target = parseInt(match[0].replace(/,/g, ''));
            if (target > 0) {
                el.dataset.animated = "true";
                animateValue(el, 0, target, 1200, text);
            }
        }
    });
}

function animateValue(el, start, end, duration, template) {
    const startTime = performance.now();
    const prefix = template.match(/^[^\d]*/)[0] || '';
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (end - start) * eased);
        el.innerText = prefix + new Intl.NumberFormat('en-IN').format(current);
        if (progress < 1) requestAnimationFrame(update);
        else el.innerText = template;
    }
    requestAnimationFrame(update);
}

// ========== VISION PANEL ==========
function updateVisionPanel(result) {
    if (!result || !result.analyzed) return;
    const el = (id) => document.getElementById(id);

    const edEl = el("vision-edge-density");
    if (edEl) edEl.innerText = (result.edge_density || 0).toFixed(3);
    const alEl = el("vision-activity-level");
    if (alEl) alEl.innerText = result.activity_level || "unknown";
    const brEl = el("vision-brightness");
    if (brEl) brEl.innerText = (result.brightness || 0).toFixed(1);
    const diEl = el("vision-dimensions");
    if (diEl) diEl.innerText = result.dimensions || "—";
    const obEl = el("vision-observation");
    if (obEl) obEl.innerText = result.observation || "";
}

// ========== TRACE RENDERER ==========
function appendTraceStep(type, description, data) {
    const log = document.getElementById("trace-log");
    if (!log) return;

    const icons = { plan: "📋", tool_call: "🔧", check: "🔍", replan: "🔄", deliver: "📊", system: "⚡", error: "❌" };
    const icon = icons[type] || "•";

    const item = document.createElement("div");
    item.className = "tl-item";
    item.style.animation = "fadeInUp 0.3s ease both";

    const dotClass = type === "deliver" ? "done" : type === "error" ? "pending" : "done";
    let detail = description;
    if (data && data.tool) detail += ` → ${data.tool}`;
    if (data && data.result && typeof data.result === "object") {
        const preview = data.result.assessment || data.result.observation || data.result.description || "";
        if (preview) detail += `: ${preview}`;
    }

    const now = new Date();
    const time = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}`;

    item.innerHTML = `
        <div class="tl-dots"><span class="tl-dot ${dotClass}"></span><span class="tl-line"></span></div>
        <div class="tl-body">
            <div class="tl-row"><strong>${icon} ${description}</strong><span class="tl-time">${time}</span></div>
            ${data && data.tool ? `<p style="font-size:10px;color:var(--text-muted);font-family:'JetBrains Mono',monospace">${data.tool}</p>` : ''}
        </div>
    `;

    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
}

// ========== PROJECT INFO ==========
async function loadProjectInfo(projectId) {
    let res, data;
    try {
        res = await fetch(`/api/project?project_id=${projectId}`);
        if (!res.ok) return;
        data = await res.json();
    } catch { return; }
    if (data.error) return;

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };

    set("proj-name", data.name || "Infrastructure Project");
    set("proj-desc", data.description || "");
    set("proj-location", data.location_name || "Zone");

    const pill = document.getElementById("proj-status-pill");
    if (pill) pill.innerText = data.status || "UNDER VERIFICATION";

    set("proj-agency", data.implementing_agency || "Municipal Corp.");
    set("metric-sanctioned", formatINR(data.sanctioned_amount));
    set("metric-released", formatINR(data.released_amount));

    const relPct = data.released_percentage || (data.sanctioned_amount ? Math.round((data.released_amount / data.sanctioned_amount) * 100) : 0);
    set("metric-released-pct", `(${relPct}%)`);

    const balance = (data.sanctioned_amount || 0) - (data.released_amount || 0);
    set("fin-balance", formatINR(balance));

    const barFill = document.getElementById("bar-released");
    if (barFill) barFill.style.width = `${relPct}%`;
    set("bar-released-label", `${relPct}% Released`);
    set("bar-claimed-label", `${100 - relPct}% Remaining`);

    set("metric-claimed", formatINR(data.claimed_amount));
    set("metric-claimed-pct", `${data.claimed_percentage || 0}%`);
    set("metric-completion", `${data.claimed_percentage || 0}%`);

    setTimeout(animateCounters, 200);
}

// ========== MONEY TRAIL ==========
async function loadMoneyTrail(projectId) {
    let res, data;
    try {
        res = await fetch(`/api/money-trail?project_id=${projectId}`);
        if (!res.ok) return;
        data = await res.json();
    } catch { return; }

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };

    set("trail-sanctioned", formatINR(data.sanctioned_amount));
    set("trail-released", formatINR(data.released_amount));
    set("trail-claimed", formatINR(data.claimed_amount));

    const sanctioned = data.sanctioned_amount || 0;
    const released = data.released_amount || 0;
    const claimed = data.claimed_amount || 0;
    const releasedPct = sanctioned > 0 ? ((released / sanctioned) * 100).toFixed(1) : 0;
    const claimedPct = sanctioned > 0 ? ((claimed / sanctioned) * 100).toFixed(1) : 0;

    set("badge-released-pct", `${releasedPct}% DISBURSED`);
    set("badge-claimed-pct", `${claimedPct}% WORK CLAIM`);

    const barReleased = document.getElementById("bar-released");
    const barClaimed = document.getElementById("bar-claimed");
    if (barReleased) setTimeout(() => { barReleased.style.width = `${Math.min(releasedPct, 100)}%`; }, 100);
    if (barClaimed) setTimeout(() => { barClaimed.style.width = `${Math.min(claimedPct, 100)}%`; }, 100);

    const callout = document.getElementById("money-callout");
    const calloutText = document.getElementById("money-callout-text");
    if (callout && calloutText && claimed > released && released > 0) {
        calloutText.innerText = `Notice: Contractor claims ₹${(claimed/100000).toFixed(1)}L but only ₹${(released/100000).toFixed(1)}L released.`;
        callout.style.display = "flex";
    } else if (callout) {
        callout.style.display = "none";
    }

    const listContainer = document.getElementById("financial-evidence-list");
    if (listContainer) {
        listContainer.innerHTML = "";
        if (data.financial_evidence) {
            data.financial_evidence.forEach(item => {
                const row = document.createElement("div");
                row.style.cssText = "font-size:12px;color:var(--text-secondary);padding:6px 0;border-bottom:1px solid rgba(124,143,255,0.06)";
                row.innerText = `${item.source_name}: ${item.observation}`;
                listContainer.appendChild(row);
            });
        }
    }
}

// ========== EVIDENCE GRAPH ==========
async function loadEvidenceGraph(projectId) {
    let res, data;
    try {
        res = await fetch(`/api/evidence-graph?project_id=${projectId}`);
        if (!res.ok) return;
        data = await res.json();
    } catch { return; }

    if (data.claims && data.claims.length > 0) {
        const claim = data.claims[0];
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
        set("claim-ref-tag", claim.claim_ref || "CLAIM-REF");
        set("claim-desc-text", claim.description || "");
        set("claim-val-text", `${claim.claimed_value} ${claim.unit}`);
        set("claim-by-text", claim.claimed_by || "Contractor");
    }

    const container = document.getElementById("evidence-nodes-container");
    if (container) container.innerHTML = "";

    currentEvidenceIds = [];
    if (data.evidence && data.evidence.length > 0) {
        data.evidence.forEach(node => {
            currentEvidenceIds.push(node.id);
        });
    }

    // Update constellation nodes with live data
    updateConstellationFromAPI(data);
}

function updateConstellationFromAPI(data) {
    if (!data.evidence) return;

    const nodeMap = {
        0: document.querySelector("#cnode-e1 .c-name"),
        1: document.querySelector("#cnode-e4 .c-name"),
        2: document.querySelector("#cnode-e3 .c-name"),
        3: document.querySelector("#cnode-e2 .c-name"),
        4: document.querySelector("#cnode-e5 .c-name"),
        5: document.querySelector("#cnode-e6 .c-name"),
    };

    data.evidence.forEach((ev, i) => {
        if (i < 6 && nodeMap[i]) {
            nodeMap[i].innerText = ev.source_name || nodeMap[i].innerText;
        }
    });
}

// ========== INVESTIGATION STATUS ==========
async function loadInvestigationStatus(projectId) {
    let res, data;
    try {
        res = await fetch(`/api/investigation-status?project_id=${projectId}`);
        if (!res.ok) return;
        data = await res.json();
    } catch { return; }

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };

    set("headline-status", data.current_status_headline || "Analyzing Contradictions");

    const timeline = document.getElementById("stages-timeline");
    if (timeline) {
        timeline.innerHTML = "";
        if (data.completed_stages) {
            data.completed_stages.forEach(stage => {
                const item = document.createElement("div");
                item.className = "timeline-stage completed";
                item.innerHTML = `<div class="stage-check">✓</div><span>${stage.name}</span>`;
                timeline.appendChild(item);
            });
        }
    }

    set("decision-state-tag", data.final_state || "HUMAN REVIEW REQUIRED");
    set("decision-summary-text", data.human_review_notice || "Verification pipeline complete.");

    if (data.human_review_notice) {
        set("review-notice-text", data.human_review_notice);
    }

    const bulletsList = document.getElementById("explanation-found-bullets");
    if (bulletsList) {
        bulletsList.innerHTML = "";
        if (data.evidence_grounded_explanation && data.evidence_grounded_explanation.what_sentinel_found) {
            data.evidence_grounded_explanation.what_sentinel_found.forEach(bullet => {
                const li = document.createElement("li");
                li.innerText = bullet;
                bulletsList.appendChild(li);
            });
            set("explanation-why-matters", data.evidence_grounded_explanation.why_this_matters || "");
        }
    }

    if (data.historical_precedent) {
        set("memory-plain-explanation", data.historical_precedent.context_summary || "");
        set("memory-precedent-rule", data.historical_precedent.precedent_rule || "");
        set("memory-badge-label", `🧠 ${data.historical_precedent.label || "CASE MEMORY"}`);
        set("memory-title", `Pattern: ${data.historical_precedent.pattern_type || ""}`);
    }

    updateVerdictBanner(data);

    if (data.final_state_raw) {
        updateStarProgress(data.final_state_raw);
    }
}

// ========== VERDICT BANNER ==========
function updateVerdictBanner(statusData) {
    const section = document.getElementById("verdict-banner-section");
    const banner = document.getElementById("verdict-banner");
    if (!section || !banner) return;

    const set = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    const stateRaw = statusData.final_state_raw || "";
    const explanation = statusData.evidence_grounded_explanation || {};

    if (stateRaw.includes("CONTRADICTED") || stateRaw.includes("HUMAN_REVIEW")) {
        set("verdict-banner-icon", "⚠");
        set("verdict-banner-headline", "Evidence Discrepancy Detected");
        set("verdict-banner-detail", explanation.why_this_matters || "Evidence does not reconcile.");
        set("verdict-banner-tag", stateRaw.replace(/_/g, " "));
    } else if (stateRaw.includes("SUPPORTED")) {
        set("verdict-banner-icon", "✓");
        set("verdict-banner-headline", "Evidence Supports Claim");
        set("verdict-banner-detail", "All sources consistent.");
        set("verdict-banner-tag", "VERIFIED");
    }

    section.style.display = "";
}

// ========== RISK CARD ACTIONS ==========
(function initRiskCard() {
    const btns = {
        hold: document.getElementById("btn-hold-funds"),
        flag: document.getElementById("btn-flag-audit"),
        release: document.getElementById("btn-release-funds"),
    };
    if (!btns.hold) return;

    const labels = {
        hold: "HELD — Pending Site Inspection",
        flag: "FLAGGED — Sent for Formal Audit",
        release: "RELEASED — Officer Decision Recorded",
    };
    const colors = { hold: "#FBBF24", flag: "#F87171", release: "#34D399" };

    Object.entries(btns).forEach(([key, btn]) => {
        btn.addEventListener("click", () => {
            Object.values(btns).forEach(b => {
                b.classList.remove("chosen-active");
                b.classList.add("chosen");
            });
            btn.classList.remove("chosen");
            btn.classList.add("chosen-active");

            let rec = document.querySelector(".risk-rec-text span");
            if (rec) {
                rec.innerHTML = "<strong>Decision Recorded:</strong> " + labels[key]
                    + " <span style='opacity:0.5;font-size:10px;'>(" + new Date().toLocaleTimeString() + ")</span>";
            }
            let ring = document.getElementById("risk-score-arc");
            if (ring) ring.style.stroke = colors[key];
        });
    });
})();

// ========== STAR FIELD ==========
(function initStarField() {
    const canvas = document.getElementById("star-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    let stars = [], shooters = [], nebulae = [];

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = Math.max(window.innerHeight, document.documentElement.scrollHeight);
    }

    function createStars() {
        stars = [];
        const count = Math.min(Math.floor((canvas.width * canvas.height) / 2500), 600);
        const colors = ['#fff', '#C4D9FF', '#A0C4FF', '#BDB2FF', '#8BE9FD'];
        for (let i = 0; i < count; i++) {
            stars.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                r: Math.random() * 1.6 + 0.3,
                a: Math.random() * 0.6 + 0.2,
                drift: (Math.random() - 0.5) * 0.12,
                speed: Math.random() * 0.008 + 0.002,
                phase: Math.random() * Math.PI * 2,
                color: colors[Math.floor(Math.random() * colors.length)]
            });
        }
    }

    function createNebulae() {
        nebulae = [];
        const nColors = ['96,165,250', '167,139,250', '34,211,238', '52,211,153'];
        for (let i = 0; i < 5; i++) {
            nebulae.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height * 0.7 + canvas.height * 0.1,
                rx: 140 + Math.random() * 220,
                ry: 70 + Math.random() * 120,
                color: nColors[i % nColors.length],
                phase: Math.random() * Math.PI * 2
            });
        }
    }

    let frame = 0;
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        frame++;
        const t = frame * 0.008;

        for (const n of nebulae) {
            const pulse = 0.035 + Math.sin(t * 0.4 + n.phase) * 0.018;
            const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.rx);
            g.addColorStop(0, `rgba(${n.color},${pulse})`);
            g.addColorStop(1, `rgba(${n.color},0)`);
            ctx.fillStyle = g;
            ctx.beginPath();
            ctx.ellipse(n.x, n.y, n.rx, n.ry, 0, 0, Math.PI * 2);
            ctx.fill();
        }

        for (const s of stars) {
            const twinkle = s.a * (0.55 + 0.45 * Math.sin(frame * s.speed * 18 + s.phase));
            ctx.globalAlpha = twinkle;
            ctx.fillStyle = s.color;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
            ctx.fill();

            if (s.r > 1.2) {
                ctx.globalAlpha = twinkle * 0.12;
                ctx.beginPath();
                ctx.arc(s.x, s.y, s.r * 3, 0, Math.PI * 2);
                ctx.fill();
            }

            s.y += s.drift;
            if (s.y < -5) s.y = canvas.height + 5;
            if (s.y > canvas.height + 5) s.y = -5;
        }
        ctx.globalAlpha = 1;

        if (Math.random() < 0.007 && shooters.length < 3) {
            const sx = Math.random() * canvas.width;
            const sy = Math.random() * canvas.height * 0.5;
            const angle = Math.PI / 4 + Math.random() * Math.PI / 5;
            shooters.push({ x: sx, y: sy, vx: Math.cos(angle) * 7, vy: Math.sin(angle) * 5, life: 1, len: 50 + Math.random() * 70 });
        }

        for (let i = shooters.length - 1; i >= 0; i--) {
            const sh = shooters[i];
            sh.x += sh.vx;
            sh.y += sh.vy;
            sh.life -= 0.016;
            if (sh.life <= 0) { shooters.splice(i, 1); continue; }
            const tx = sh.x - sh.vx * (sh.len / 7);
            const ty = sh.y - sh.vy * (sh.len / 7);
            const g = ctx.createLinearGradient(tx, ty, sh.x, sh.y);
            g.addColorStop(0, 'rgba(255,255,255,0)');
            g.addColorStop(1, `rgba(255,255,255,${sh.life * 0.7})`);
            ctx.strokeStyle = g;
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(tx, ty);
            ctx.lineTo(sh.x, sh.y);
            ctx.stroke();
        }

        requestAnimationFrame(draw);
    }

    resize();
    createStars();
    createNebulae();
    draw();
    window.addEventListener("resize", () => { resize(); createStars(); createNebulae(); });

    let resizeTimer;
    new ResizeObserver(() => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            const newH = document.documentElement.scrollHeight;
            if (Math.abs(canvas.height - newH) > 100) {
                canvas.height = newH;
                createStars();
            }
        }, 200);
    }).observe(document.body);
})();
