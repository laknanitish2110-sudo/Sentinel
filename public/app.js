// SENTINEL Citizen Experience Frontend Logic
document.addEventListener("DOMContentLoaded", () => {
    initSentinelApp();
});

async function initSentinelApp() {
    try {
        await loadProjectInfo();
        await loadMoneyTrail();
        await loadEvidenceGraph();
        await loadInvestigationStatus();
    } catch (err) {
        console.error("Failed to load Sentinel public data:", err);
    }
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
async function loadProjectInfo() {
    const res = await fetch("/api/project");
    const data = await res.json();

    document.getElementById("proj-name").innerText = data.name || "Ward 7 Drainage Improvement";
    document.getElementById("proj-desc").innerText = data.description || "";
    document.getElementById("proj-location").innerText = data.location_name || "Ward 7";
    document.getElementById("proj-status-pill").innerText = data.status || "UNDER VERIFICATION";

    document.getElementById("metric-sanctioned").innerText = formatINR(data.sanctioned_amount);
    document.getElementById("metric-released").innerText = formatINR(data.released_amount);
    document.getElementById("metric-released-pct").innerText = `${data.released_percentage}% of total budget`;
    
    document.getElementById("metric-claimed").innerText = formatINR(data.claimed_amount);
    document.getElementById("metric-claimed-pct").innerText = `${data.claimed_percentage}% physical claim`;
    document.getElementById("metric-completion").innerText = `${data.claimed_percentage}%`;
}

// SCREEN 2: MONEY TRAIL
async function loadMoneyTrail() {
    const res = await fetch("/api/money-trail");
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
async function loadEvidenceGraph() {
    const res = await fetch("/api/evidence-graph");
    const data = await res.json();

    // Render Claim Node
    if (data.claims && data.claims.length > 0) {
        const claim = data.claims[0];
        document.getElementById("claim-ref-tag").innerText = claim.claim_ref || "CLAIM-REF";
        document.getElementById("claim-desc-text").innerText = claim.description || "";
        document.getElementById("claim-val-text").innerText = `${claim.claimed_value} ${claim.unit}`;
        document.getElementById("claim-by-text").innerText = claim.claimed_by || "Contractor";
    }

    // Render Evidence Nodes
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
async function loadInvestigationStatus() {
    const res = await fetch("/api/investigation-status");
    const data = await res.json();

    document.getElementById("headline-status").innerText = data.current_status_headline || "Sentinel is reviewing project evidence";

    // Render Timeline
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

    // Render Final State
    document.getElementById("decision-state-tag").innerText = data.final_state || "HUMAN REVIEW REQUIRED";
    document.getElementById("decision-summary-text").innerText = data.human_review_notice || "Sentinel completed verification pipeline.";

    // Render Human Review Box
    if (data.human_review_notice) {
        document.getElementById("human-review-box").style.display = "flex";
        document.getElementById("review-notice-text").innerText = data.human_review_notice;
    } else {
        document.getElementById("human-review-box").style.display = "none";
    }

    // Render Explanation
    if (data.evidence_grounded_explanation) {
        document.getElementById("explanation-body-text").innerText = data.evidence_grounded_explanation;
    }

    // Render Case Memory
    const memCard = document.getElementById("case-memory-card");
    if (data.learned_case_memory) {
        memCard.style.display = "block";
        document.getElementById("memory-title").innerText = `Pattern: ${data.learned_case_memory.pattern_type}`;
        document.getElementById("memory-plain-explanation").innerText = data.learned_case_memory.plain_explanation;
        document.getElementById("memory-precedent-rule").innerText = data.learned_case_memory.precedent_rule;
    } else {
        memCard.style.display = "none";
    }
}
