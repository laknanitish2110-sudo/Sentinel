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
}

async function loadProjectData(projectId) {
    try {
        updateStateMachine("step-discover");
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

    try {
        btn.innerText = "INITIALIZING AGENTS...";
        btn.disabled = true;

        // Stage 1: Discovery
        updateStateMachine("step-discover");
        btn.innerText = "STAGE 1: DISCOVERING...";
        await sleep(600);

        // Stage 2: Investigation
        updateStateMachine("step-investigate");
        btn.innerText = "STAGE 2: AGENTS INVESTIGATING...";
        await sleep(500);

        // Stage 3: Analyzing
        updateStateMachine("step-analyzing");
        btn.innerText = "STAGE 3: CROSS-CHECKING EVIDENCE...";
        await sleep(500);

        // Stage 4: Evidence Graph
        updateStateMachine("step-graph");
        btn.innerText = "STAGE 4: BUILDING EVIDENCE GRAPH...";
        await sleep(400);

        // Actual API call
        const res = await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_id: currentProjectId })
        });
        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        await res.json();

        // Stage 5: Conflict
        updateStateMachine("step-conflict");
        btn.innerText = "STAGE 5: CONFLICTS DETECTED...";
        await sleep(500);

        // Stage 6: Review
        updateStateMachine("step-review");
        btn.innerText = "STAGE 6: HUMAN REVIEW REQUIRED";
        await sleep(400);

        showSuccess("Investigation complete. Evidence pipeline executed successfully.");
        await loadProjectData(currentProjectId);

    } catch (err) {
        console.error("Failed to run investigation:", err);
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
