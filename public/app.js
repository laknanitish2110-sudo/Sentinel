// SENTINEL Citizen Experience Frontend Logic — Full Investigation Loop
document.addEventListener("DOMContentLoaded", () => {
    initSentinelApp();
});

let currentProjectId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";
let currentEvidenceIds = [];
let investigationRunning = false;

async function initSentinelApp() {
    setupEventListeners();
    animateCounters();
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

    // Make progress bar tabs clickable — scroll to corresponding section
    document.querySelectorAll(".sm-step").forEach(step => {
        step.style.cursor = "pointer";
        step.addEventListener("click", () => {
            const targetId = step.dataset.target;
            if (targetId) {
                const target = document.getElementById(targetId);
                if (target) target.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
}

async function loadProjectData(projectId) {
    try {
        await loadProjectInfo(projectId);
        await loadMoneyTrail(projectId);
        await loadEvidenceGraph(projectId);
        await loadInvestigationStatus(projectId);
    } catch (err) {
        console.error("Failed to load Sentinel public data:", err);
        showError("Failed to load project data. Please refresh the page.");
    }
}

// ========== ANIMATED INVESTIGATION FLOW ==========
async function runInvestigationFlow() {
    if (investigationRunning) return;
    investigationRunning = true;

    const btn = document.getElementById("btn-trigger-investigation");
    const origText = btn.innerText;
    const traceLog = document.getElementById("trace-log");
    const traceDot = document.querySelector(".trace-dot");
    const traceStatus = document.getElementById("trace-status-text");

    try {
        btn.innerText = "INITIALIZING AGENT...";
        btn.disabled = true;
        traceLog.innerHTML = "";
        traceDot.className = "trace-dot running";
        traceStatus.innerText = "Agent initializing...";

        // Reveal progress bar
        const smSection = document.getElementById("state-machine-section");
        if (smSection) {
            smSection.style.display = "";
            smSection.style.animation = "fadeInUp 0.4s ease both";
            smSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }

        // Stage 1: Discovery
        updateStateMachine("step-discover");
        appendTraceStep("system", "Agent waking up — loading project context...");
        await sleep(400);

        // Stage 2: Investigation
        updateStateMachine("step-investigate");
        traceStatus.innerText = "Agent running investigation loop...";
        appendTraceStep("system", "Sending project to autonomous investigation agent...");
        await sleep(300);

        // Actual agentic API call
        updateStateMachine("step-analyzing");
        const res = await fetch("/api/agent-investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_id: currentProjectId })
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const agentResult = await res.json();

        // Render the agent trace steps with animation
        if (agentResult.trace && agentResult.trace.length > 0) {
            for (let i = 0; i < agentResult.trace.length; i++) {
                const step = agentResult.trace[i];
                await sleep(250);
                appendTraceStep(step.step_type, step.description, step.data);

                // Update state machine based on step type
                if (step.step_type === "plan" || step.step_type === "replan") updateStateMachine("step-investigate");
                if (step.step_type === "tool_call" && step.data.tool === "analyze_photo" && step.data.result) updateVisionPanel(step.data.result);
                if (step.step_type === "tool_call" && (step.data.tool === "cross_check_values" || step.description.includes("Cross-check"))) updateStateMachine("step-analyzing");
                if (step.step_type === "tool_call" && (step.data.tool === "flag_discrepancy" || step.description.includes("Discrepancy"))) updateStateMachine("step-conflict");
                if (step.step_type === "tool_call" && (step.data.tool === "search_precedents" || step.description.includes("case memory"))) updateStateMachine("step-graph");
                if (step.step_type === "tool_call" && (step.data.tool === "verify_financial_trail" || step.description.includes("financial"))) updateStateMachine("step-graph");
                if (step.step_type === "deliver") {
                    const state = step.data.final_state || "";
                    if (state.includes("HUMAN_REVIEW")) updateStateMachine("step-review");
                    else updateStateMachine("step-review");
                }
            }
        }

        // Update trace meta
        const iterations = agentResult.iterations || 0;
        const toolCalls = (agentResult.trace || []).filter(s => s.step_type === "tool_call").length;
        document.getElementById("trace-iteration-count").innerText = `${iterations} iteration${iterations !== 1 ? 's' : ''}`;
        document.getElementById("trace-tool-count").innerText = `${toolCalls} tool call${toolCalls !== 1 ? 's' : ''}`;

        // Final state
        const finalState = agentResult.final_state || "UNKNOWN";
        traceDot.className = "trace-dot complete";
        traceStatus.innerText = `Agent complete — ${finalState.replace(/_/g, ' ')}`;

        if (finalState.includes("HUMAN_REVIEW")) {
            updateStateMachine("step-review");
        } else if (finalState.includes("CORRECTION")) {
            updateStateMachine("step-correction");
        }

        showSuccess(`Agentic investigation complete: ${finalState.replace(/_/g, ' ')}. ${agentResult.contradiction_count || 0} discrepancies found.`);

        // Reload data sections without resetting state machine
        await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_id: currentProjectId })
        });

        await loadProjectInfo(currentProjectId);
        await loadMoneyTrail(currentProjectId);
        await loadEvidenceGraph(currentProjectId);
        await loadInvestigationStatus(currentProjectId);

    } catch (err) {
        console.error("Failed to run investigation:", err);
        traceDot.className = "trace-dot error";
        traceStatus.innerText = "Agent encountered an error";
        appendTraceStep("error", `Investigation failed: ${err.message}`, {});
        showError("Investigation failed. Please try again.");
    } finally {
        btn.innerText = origText;
        btn.disabled = false;
        investigationRunning = false;
    }
}

async function submitAuditorCorrection() {
    const interp = document.getElementById("corr-interp").value;
    const reason = document.getElementById("corr-reason").value;

    const btn = document.getElementById("btn-submit-correction");
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
        console.error("Failed to submit correction:", err);
        showError("Correction submission failed. Please try again.");
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
            if (id === activeStepId) {
                el.classList.add("active");
            } else if (activeIdx >= 0 && idx < activeIdx) {
                el.classList.add("completed");
            }
        }
    });
}

// ========== NOTIFICATIONS ==========
function showError(msg) {
    showToast(msg, "#DC2626", "rgba(220,38,38,0.15)");
}

function showSuccess(msg) {
    showToast(msg, "#10B981", "rgba(16,185,129,0.15)");
}

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

// ========== ANIMATED COUNTERS ==========
function animateCounters() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const text = el.innerText;
                const match = text.match(/[\d,]+/);
                if (match) {
                    const target = parseInt(match[0].replace(/,/g, ''));
                    if (target > 0 && !el.dataset.animated) {
                        el.dataset.animated = "true";
                        animateValue(el, 0, target, 1200, text);
                    }
                }
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll(".metric-val, .amount-display").forEach(el => {
        observer.observe(el);
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
        if (progress < 1) {
            requestAnimationFrame(update);
        } else {
            el.innerText = template;
        }
    }
    requestAnimationFrame(update);
}

// ========== UTILITIES ==========
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function formatINR(val) {
    if (val === null || val === undefined) return "₹0";
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(val);
}

// ========== VISION PANEL ==========
function updateVisionPanel(result) {
    if (!result || !result.analyzed) return;

    const edgeDensity = result.edge_density || 0;
    const activity = result.activity_level || "unknown";
    const brightness = result.brightness || 0;
    const dims = result.dimensions || "—";
    const colors = result.dominant_colors || {};
    const obs = result.observation || "";

    const el = (id) => document.getElementById(id);

    el("vision-edge-density").innerText = edgeDensity.toFixed(3);
    el("vision-activity-level").innerText = activity;
    el("vision-brightness").innerText = brightness.toFixed(1);
    el("vision-dimensions").innerText = dims;
    el("vision-observation").innerText = obs;

    setTimeout(() => {
        el("vision-edge-bar").style.width = `${Math.min(edgeDensity * 333, 100)}%`;
        el("vision-brightness-bar").style.width = `${(brightness / 255) * 100}%`;
    }, 100);

    const badge = el("vision-activity-badge");
    badge.innerText = `${activity.toUpperCase()} ACTIVITY`;
    badge.className = "vision-badge " + (activity === "high" ? "high" : activity === "low" ? "low" : "");

    const dots = el("vision-panel").querySelectorAll(".vision-activity-dots .dot");
    const level = activity === "high" ? 3 : activity === "moderate" ? 2 : 1;
    dots.forEach((d, i) => d.classList.toggle("active", i < level));

    if (colors.r !== undefined) {
        el("swatch-r").style.background = `rgb(${Math.round(colors.r)},${Math.round(colors.g)},${Math.round(colors.b)})`;
    }

    el("vision-analysis-tier").style.animation = "fadeInUp 0.5s ease both";
}

// ========== AGENT TRACE RENDERER ==========
function appendTraceStep(type, description, data) {
    const log = document.getElementById("trace-log");
    if (!log) return;

    const step = document.createElement("div");
    step.className = `trace-step trace-${type}`;
    step.style.animation = "fadeInUp 0.3s ease both";

    const icons = {
        plan: "📋", tool_call: "🔧", check: "🔍", replan: "🔄",
        deliver: "📊", system: "⚡", error: "❌"
    };
    const labels = {
        plan: "PLAN", tool_call: "TOOL", check: "CHECK", replan: "RE-PLAN",
        deliver: "DELIVER", system: "SYSTEM", error: "ERROR"
    };

    let icon = icons[type] || "•";
    let label = labels[type] || type.toUpperCase();
    if (type === "tool_call" && data && data.tool === "analyze_photo") {
        icon = "📸";
        label = "VISION";
    }

    let detailHTML = "";
    if (data && typeof data === "object" && Object.keys(data).length > 0) {
        if (data.tool) {
            detailHTML = `<span class="trace-tool-name">${data.tool}</span>`;
        }
        if (data.result && typeof data.result === "object") {
            const resultPreview = data.result.assessment || data.result.observation ||
                                  data.result.description || data.result.reason ||
                                  (data.result.consistent !== undefined ? (data.result.consistent ? "Values consistent" : `INCONSISTENT: ${data.result.discrepancy_pct}% gap`) : "");
            if (resultPreview) {
                detailHTML += `<div class="trace-result">${resultPreview}</div>`;
            }
        }
        if (data.conclusion) {
            detailHTML += `<div class="trace-result trace-conclusion">${data.conclusion}</div>`;
        }
        if (data.final_state) {
            detailHTML += `<span class="trace-state-badge">${data.final_state.replace(/_/g, ' ')}</span>`;
        }
    }

    step.innerHTML = `
        <div class="trace-step-header">
            <span class="trace-icon">${icon}</span>
            <span class="trace-label">${label}</span>
            <span class="trace-desc">${description}</span>
        </div>
        ${detailHTML ? `<div class="trace-detail">${detailHTML}</div>` : ""}
    `;

    log.appendChild(step);
    log.scrollTop = log.scrollHeight;
}

// ========== SCREEN 1: PROJECT DISCOVERY ==========
async function loadProjectInfo(projectId) {
    const res = await fetch(`/api/project?project_id=${projectId}`);
    if (!res.ok) throw new Error(`Project API error: ${res.status}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    document.getElementById("proj-name").innerText = data.name || "Infrastructure Project";
    document.getElementById("proj-desc").innerText = data.description || "";
    document.getElementById("proj-location").innerText = data.location_name || "Zone";
    document.getElementById("proj-status-pill").innerText = data.status || "UNDER VERIFICATION";

    document.getElementById("metric-sanctioned").innerText = formatINR(data.sanctioned_amount);
    document.getElementById("metric-released").innerText = formatINR(data.released_amount);
    document.getElementById("metric-released-pct").innerText = `${data.released_percentage || 0}% of total budget`;

    document.getElementById("metric-claimed").innerText = formatINR(data.claimed_amount);
    document.getElementById("metric-claimed-pct").innerText = `${data.claimed_percentage || 0}% physical claim`;
    document.getElementById("metric-completion").innerText = `${data.claimed_percentage || 0}%`;

    setTimeout(animateCounters, 100);
}

// ========== SCREEN 2: MONEY TRAIL ==========
async function loadMoneyTrail(projectId) {
    const res = await fetch(`/api/money-trail?project_id=${projectId}`);
    if (!res.ok) throw new Error(`Money trail API error: ${res.status}`);
    const data = await res.json();

    document.getElementById("trail-sanctioned").innerText = formatINR(data.sanctioned_amount);
    document.getElementById("trail-released").innerText = formatINR(data.released_amount);
    document.getElementById("trail-claimed").innerText = formatINR(data.claimed_amount);

    // Update percentage badges dynamically
    const sanctioned = data.sanctioned_amount || 0;
    const released = data.released_amount || 0;
    const claimed = data.claimed_amount || 0;
    const releasedPct = sanctioned > 0 ? ((released / sanctioned) * 100).toFixed(1) : 0;
    const claimedPct = sanctioned > 0 ? ((claimed / sanctioned) * 100).toFixed(1) : 0;

    const relBadge = document.getElementById("badge-released-pct");
    if (relBadge) relBadge.innerText = `${releasedPct}% DISBURSED`;
    const clmBadge = document.getElementById("badge-claimed-pct");
    if (clmBadge) clmBadge.innerText = `${claimedPct}% WORK CLAIM`;

    // Discrepancy bar
    const barContainer = document.getElementById("discrepancy-bar-container");
    if (barContainer && sanctioned > 0) {
        barContainer.style.display = "block";
        const barReleased = document.getElementById("bar-released");
        const barClaimed = document.getElementById("bar-claimed");
        if (barReleased) setTimeout(() => { barReleased.style.width = `${Math.min(releasedPct, 100)}%`; }, 100);
        if (barClaimed) setTimeout(() => { barClaimed.style.width = `${Math.min(claimedPct, 100)}%`; }, 100);
        const relLabel = document.getElementById("bar-released-label");
        const clmLabel = document.getElementById("bar-claimed-label");
        const gapLabel = document.getElementById("bar-gap-label");
        if (relLabel) relLabel.innerText = `${releasedPct}% released`;
        if (clmLabel) clmLabel.innerText = `${claimedPct}% claimed`;
        if (gapLabel && claimed > released) {
            const gapPct = (((claimed - released) / sanctioned) * 100).toFixed(1);
            gapLabel.innerText = `⚠ ${gapPct}% gap`;
        }
    }

    // Dynamic callout
    const callout = document.getElementById("money-callout");
    const calloutText = document.getElementById("money-callout-text");
    if (callout && calloutText && claimed > released && released > 0) {
        const claimedL = (claimed / 100000).toFixed(1);
        const releasedL = (released / 100000).toFixed(1);
        calloutText.innerText = `Notice: The contractor claims ₹${claimedL}L of work done, but the government has only released ₹${releasedL}L. That's a gap worth investigating.`;
        callout.style.display = "flex";
    } else if (callout) {
        callout.style.display = "none";
    }

    const listContainer = document.getElementById("financial-evidence-list");
    listContainer.innerHTML = "";

    if (data.financial_evidence && data.financial_evidence.length > 0) {
        data.financial_evidence.forEach((item, idx) => {
            const row = document.createElement("div");
            row.className = "evidence-item-row";
            row.style.animationDelay = `${idx * 0.1}s`;
            row.style.animation = "fadeInUp 0.4s ease both";

            const amountText = item.amount ? formatINR(item.amount) : "Verified Document";
            let relBadge, relColor;
            if (item.relationship === "SUPPORTS") {
                relBadge = "✓ Verified"; relColor = "var(--color-supports)";
            } else if (item.relationship === "CONTRADICTS") {
                relBadge = "✕ Conflict"; relColor = "var(--color-contradicts)";
            } else if (item.relationship === "INSUFFICIENT") {
                relBadge = "⚠ Missing"; relColor = "var(--color-insufficient)";
            } else {
                relBadge = "ℹ Reference"; relColor = "var(--color-neutral)";
            }

            row.innerHTML = `
                <div class="ev-info">
                    <h4>${item.source_name} (${item.document_id})</h4>
                    <p>${item.observation}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 800; font-size: 15px;">${amountText}</div>
                    <div style="font-size: 12px; color: ${relColor}; margin-top: 4px; font-weight: 700;">${relBadge}</div>
                </div>
            `;
            listContainer.appendChild(row);
        });
    } else {
        listContainer.innerHTML = "<p style='color: var(--text-muted);'>No financial evidence records found.</p>";
    }
}

// ========== SCREEN 3: EVIDENCE GRAPH ==========
async function loadEvidenceGraph(projectId) {
    const res = await fetch(`/api/evidence-graph?project_id=${projectId}`);
    if (!res.ok) throw new Error(`Evidence graph API error: ${res.status}`);
    const data = await res.json();

    if (data.claims && data.claims.length > 0) {
        const claim = data.claims[0];
        document.getElementById("claim-ref-tag").innerText = claim.claim_ref || "CLAIM-REF";
        document.getElementById("claim-desc-text").innerText = claim.description || "";
        document.getElementById("claim-val-text").innerText = `${claim.claimed_value} ${claim.unit}`;
        document.getElementById("claim-by-text").innerText = claim.claimed_by || "Contractor";
    }

    const container = document.getElementById("evidence-nodes-container");
    container.innerHTML = "";

    currentEvidenceIds = [];
    if (data.evidence && data.evidence.length > 0) {
        data.evidence.forEach((node, idx) => {
            currentEvidenceIds.push(node.id);
            const card = document.createElement("div");
            const relClass = `rel-${node.relationship.toLowerCase()}`;
            card.className = `evidence-card ${relClass}`;
            card.style.animationDelay = `${idx * 0.15}s`;

            card.innerHTML = `
                <div>
                    <div class="ev-badge">
                        <span>${node.badge_icon}</span>
                        <span>${node.relationship_label}</span>
                    </div>
                    <div class="ev-header">
                        <h4>${node.source_name}</h4>
                        <div class="ev-doc-id">Document Ref: ${node.source_id}</div>
                    </div>
                    <p class="ev-obs">"${node.observation}"</p>
                </div>
                <div class="ev-footer">
                    <span>Reliability: <strong>${node.reliability}</strong></span>
                    <span>Confidence: <strong>${node.confidence_score}</strong></span>
                </div>
            `;
            container.appendChild(card);
        });
    }

    // Update evidence count badge
    const countBadge = document.getElementById("evidence-count-badge");
    if (countBadge) {
        countBadge.innerText = `${currentEvidenceIds.length} evidence nodes`;
    }
}

// ========== SCREEN 4 & 5: INVESTIGATION STATUS ==========
async function loadInvestigationStatus(projectId) {
    const res = await fetch(`/api/investigation-status?project_id=${projectId}`);
    if (!res.ok) throw new Error(`Investigation status API error: ${res.status}`);
    const data = await res.json();

    document.getElementById("headline-status").innerText = data.current_status_headline || "Sentinel Evidence Investigation Summary";

    const timeline = document.getElementById("stages-timeline");
    timeline.innerHTML = "";
    if (data.completed_stages) {
        data.completed_stages.forEach((stage, idx) => {
            const item = document.createElement("div");
            item.className = "timeline-stage completed";
            item.style.animation = "fadeInUp 0.3s ease both";
            item.style.animationDelay = `${idx * 0.1}s`;
            item.innerHTML = `
                <div class="stage-check">✓</div>
                <span>${stage.name}</span>
            `;
            timeline.appendChild(item);
        });
    }

    // Update decision node styling based on state
    const stateTag = document.getElementById("decision-state-tag");
    const decisionCard = document.getElementById("decision-node-card");
    const decisionIcon = document.getElementById("decision-icon");
    const stateRaw = data.final_state_raw || "";

    stateTag.innerText = data.final_state || "HUMAN REVIEW REQUIRED";
    document.getElementById("decision-summary-text").innerText = data.human_review_notice || "Sentinel completed verification pipeline.";

    if (stateRaw.includes("SUPPORTED") && !stateRaw.includes("PARTIALLY")) {
        decisionCard.style.borderColor = "var(--border-supports)";
        decisionCard.style.background = "var(--bg-supports)";
        stateTag.style.backgroundColor = "var(--border-supports)";
        decisionIcon.innerText = "✓";
    } else if (stateRaw.includes("CONTRADICTED")) {
        decisionCard.style.borderColor = "var(--border-contradicts)";
        decisionCard.style.background = "var(--bg-contradicts)";
        stateTag.style.backgroundColor = "var(--border-contradicts)";
        decisionIcon.innerText = "✕";
    } else if (stateRaw.includes("HUMAN_REVIEW")) {
        decisionCard.style.borderColor = "var(--border-insufficient)";
        decisionCard.style.background = "rgba(245, 158, 11, 0.1)";
        stateTag.style.backgroundColor = "var(--border-insufficient)";
        decisionIcon.innerText = "⚖️";
    } else if (stateRaw.includes("PARTIALLY")) {
        decisionCard.style.borderColor = "var(--accent-blue)";
        decisionCard.style.background = "rgba(99, 102, 241, 0.1)";
        stateTag.style.backgroundColor = "var(--accent-blue)";
        decisionIcon.innerText = "◐";
    }

    if (data.human_review_notice) {
        document.getElementById("human-review-box").style.display = "flex";
        document.getElementById("review-notice-text").innerText = data.human_review_notice;
    } else {
        document.getElementById("human-review-box").style.display = "none";
    }

    // Render Citizen Explanation Bullets
    const bulletsList = document.getElementById("explanation-found-bullets");
    bulletsList.innerHTML = "";
    if (data.evidence_grounded_explanation && data.evidence_grounded_explanation.what_sentinel_found) {
        data.evidence_grounded_explanation.what_sentinel_found.forEach((bullet, idx) => {
            const li = document.createElement("li");
            li.style.animation = "fadeInUp 0.3s ease both";
            li.style.animationDelay = `${idx * 0.15}s`;
            li.innerText = bullet;
            bulletsList.appendChild(li);
        });
        document.getElementById("explanation-why-matters").innerText = data.evidence_grounded_explanation.why_this_matters || "";
    }

    // Render Case Memory / Historical Precedent
    const memCard = document.getElementById("case-memory-card");
    if (data.historical_precedent) {
        memCard.style.display = "block";
        memCard.style.animation = "fadeInUp 0.5s ease both";
        if (data.historical_precedent.label) {
            document.getElementById("memory-badge-label").innerText = `🧠 ${data.historical_precedent.label}`;
        }
        document.getElementById("memory-title").innerText = `Pattern: ${data.historical_precedent.pattern_type}`;
        document.getElementById("memory-plain-explanation").innerText = data.historical_precedent.context_summary;
        document.getElementById("memory-precedent-rule").innerText = data.historical_precedent.precedent_rule;
    } else {
        memCard.style.display = "none";
    }
}
