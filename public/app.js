// SENTINEL Citizen Experience Frontend Logic (Phase 5)
document.addEventListener("DOMContentLoaded", () => {
    initSentinelApp();
});

let currentProjectId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";

async function initSentinelApp() {
    setupEventListeners();
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

async function runInvestigationFlow() {
    try {
        updateStateMachine("step-investigate");
        const res = await fetch("/api/investigate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ project_id: currentProjectId })
        });
        const data = await res.json();
        updateStateMachine("step-conflict");
        await loadProjectData(currentProjectId);
    } catch (err) {
        console.error("Failed to run investigation:", err);
    }
}

async function submitAuditorCorrection() {
    const interp = document.getElementById("corr-interp").value;
    const reason = document.getElementById("corr-reason").value;

    try {
        updateStateMachine("step-correction");
        const res = await fetch("/api/human-correction", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                project_id: currentProjectId,
                investigation_id: "inv_demo_phase5",
                corrected_interpretation: interp,
                reason_for_correction: reason,
                evidence_ids: ["e1-mb", "e2-photo"]
            })
        });
        const data = await res.json();
        
        const successMsg = document.getElementById("correction-success-msg");
        if (successMsg) {
            successMsg.style.display = "block";
            setTimeout(() => { successMsg.style.display = "none"; }, 5000);
        }

        updateStateMachine("step-memory");
        await loadInvestigationStatus(currentProjectId);
    } catch (err) {
        console.error("Failed to submit correction:", err);
    }
}

function updateStateMachine(activeStepId) {
    const steps = ["step-discover", "step-investigate", "step-analyzing", "step-graph", "step-conflict", "step-review", "step-correction", "step-memory", "step-second-case"];
    steps.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            if (id === activeStepId) {
                el.classList.add("active");
            } else {
                el.classList.remove("active");
            }
        }
    });
}

function formatINR(val) {
    if (val === null || val === undefined) return "₹0";
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(val);
}

// SCREEN 1: PROJECT DISCOVERY
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
}

// SCREEN 2: MONEY TRAIL
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
        data.financial_evidence.forEach(item => {
            const row = document.createElement("div");
            row.className = "evidence-item-row";
            
            const amountText = item.amount ? `${formatINR(item.amount)}` : "Verified Document";
            const relBadge = item.relationship === "SUPPORTS" ? "✓ Verified" : (item.relationship === "CONTRADICTS" ? "✕ Conflict" : "ℹ Reference");
            
            row.innerHTML = `
                <div class="ev-info">
                    <h4>${item.source_name} (${item.document_id})</h4>
                    <p>${item.observation}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: 800; font-size: 15px;">${amountText}</div>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 2px;">${relBadge}</div>
                </div>
            `;
            listContainer.appendChild(row);
        });
    } else {
        listContainer.innerHTML = "<p style='color: var(--text-muted);'>No financial evidence records found.</p>";
    }
}

// SCREEN 3: EVIDENCE GRAPH
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

    if (data.evidence && data.evidence.length > 0) {
        data.evidence.forEach(node => {
            const card = document.createElement("div");
            const relClass = `rel-${node.relationship.toLowerCase()}`;
            card.className = `evidence-card ${relClass}`;

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
}

// SCREEN 4 & 5: INVESTIGATION STATUS, WHY & CASE MEMORY
async function loadInvestigationStatus(projectId) {
    const res = await fetch(`/api/investigation-status?project_id=${projectId}`);
    if (!res.ok) throw new Error(`Investigation status API error: ${res.status}`);
    const data = await res.json();

    document.getElementById("headline-status").innerText = data.current_status_headline || "Sentinel Evidence Investigation Summary";

    const timeline = document.getElementById("stages-timeline");
    timeline.innerHTML = "";
    if (data.completed_stages) {
        data.completed_stages.forEach(stage => {
            const item = document.createElement("div");
            item.className = "timeline-stage completed";
            item.innerHTML = `
                <div class="stage-check">✓</div>
                <span>${stage.name}</span>
            `;
            timeline.appendChild(item);
        });
    }

    document.getElementById("decision-state-tag").innerText = data.final_state || "HUMAN REVIEW REQUIRED";
    document.getElementById("decision-summary-text").innerText = data.human_review_notice || "Sentinel completed verification pipeline.";

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
        data.evidence_grounded_explanation.what_sentinel_found.forEach(bullet => {
            const li = document.createElement("li");
            li.innerText = bullet;
            bulletsList.appendChild(li);
        });
        document.getElementById("explanation-why-matters").innerText = data.evidence_grounded_explanation.why_this_matters || "";
    }

    // Render Case Memory / Historical Precedent
    const memCard = document.getElementById("case-memory-card");
    if (data.historical_precedent) {
        memCard.style.display = "block";
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
