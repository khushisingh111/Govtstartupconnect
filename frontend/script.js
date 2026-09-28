const API_BASE = "";

// ============================================================ Session
let session = JSON.parse(localStorage.getItem("setu_session") || "null");

function saveSession(data, type) {
  session = { ...data, type };
  localStorage.setItem("setu_session", JSON.stringify(session));
  renderSessionLabel();
}
function clearSession() {
  session = null;
  localStorage.removeItem("setu_session");
  renderSessionLabel();
}
function authHeaders() {
  return session ? { "Authorization": `Bearer ${session.token}` } : {};
}
function renderSessionLabel() {
  const label = document.getElementById("sessionLabel");
  const authBtn = document.getElementById("authButton");
  if (session) {
    label.textContent = `Signed in — ${session.name} (${session.type === "gov" ? "Government" : "Startup"})`;
    authBtn.textContent = "Sign out";
  } else {
    label.textContent = "Not signed in";
    authBtn.textContent = "Sign in";
  }
}

// ============================================================ Avatars (company "logos")
const AVATAR_COLORS = ["#14213D", "#2E7D46", "#D97B1F", "#8A3324", "#3A5A9C", "#5A4A8A"];
function avatarFor(name) {
  const initials = name.split(/\s+/).map(w => w[0]).slice(0, 2).join("").toUpperCase();
  let hash = 0;
  for (const ch of name) hash = ch.charCodeAt(0) + ((hash << 5) - hash);
  const color = AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
  return { initials, color };
}
function avatarHtml(name, size) {
  const { initials, color } = avatarFor(name);
  const s = size || 44;
  return `<div class="avatar" style="background:${color}; width:${s}px; height:${s}px; font-size:${s * 0.36}px;">${initials}</div>`;
}
function riskBadgeHtml(level) {
  const cls = level === "Low" ? "risk-low" : level === "Medium" ? "risk-medium" : "risk-high";
  return `<span class="risk-badge ${cls}">${level} risk</span>`;
}

// ============================================================ Navigation
function goToPage(page) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.getElementById("page-" + page).classList.add("active");
  document.querySelectorAll(".nav-link").forEach(n => n.classList.toggle("active", n.dataset.page === page));
  window.scrollTo({ top: 0, behavior: "smooth" });
  if (page === "leaderboard") loadLeaderboard();
  if (page === "startup") renderStartupDeskState();
}
document.querySelectorAll(".nav-link").forEach(btn => btn.addEventListener("click", () => goToPage(btn.dataset.page)));
document.querySelectorAll("[data-goto]").forEach(btn => btn.addEventListener("click", () => {
  closeModal("authModal");
  goToPage(btn.dataset.goto);
}));

// ============================================================ Modals
function openModal(id) { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }
document.getElementById("closeModal").addEventListener("click", () => closeModal("profileModal"));
document.getElementById("closeAuthModal").addEventListener("click", () => closeModal("authModal"));
document.getElementById("profileModal").addEventListener("click", (e) => { if (e.target.id === "profileModal") closeModal("profileModal"); });
document.getElementById("authModal").addEventListener("click", (e) => { if (e.target.id === "authModal") closeModal("authModal"); });

document.getElementById("authButton").addEventListener("click", () => {
  if (session) {
    fetch(`${API_BASE}/api/auth/logout`, { method: "POST", headers: authHeaders() }).catch(() => {});
    clearSession();
    renderStartupDeskState();
  } else {
    openModal("authModal");
  }
});
document.getElementById("govSignInBtn").addEventListener("click", () => {
  document.getElementById("govLoginArea").style.display = "block";
});

// ============================================================ Health + stats
async function loadStats() {
  try {
    await fetch(`${API_BASE}/api/health`).then(r => r.json());
    document.getElementById("statHealth").textContent = "online";
  } catch (e) {
    document.getElementById("statHealth").textContent = "offline";
  }
  try {
    const board = await fetch(`${API_BASE}/api/leaderboard?limit=50`).then(r => r.json());
    document.getElementById("statCount").textContent = board.length;
    document.getElementById("statTop").textContent = board.length ? board[0].score.toFixed(1) : "—";
  } catch (e) { console.error(e); }
}

// ============================================================ Leaderboard
async function loadLeaderboard() {
  const container = document.getElementById("leaderboardCards");
  container.innerHTML = `<p class="empty-state">Loading leaderboard…</p>`;
  try {
    const board = await fetch(`${API_BASE}/api/leaderboard?limit=50`).then(r => r.json());
    if (!board.length) {
      container.innerHTML = `<p class="empty-state">No startups registered yet.</p>`;
      return;
    }
    container.innerHTML = board.map((s, i) => `
      <div class="lb-card ${i === 0 ? "top1" : i === 1 ? "top2" : i === 2 ? "top3" : ""}" data-id="${s.startup_id}">
        <div class="lb-rank">#${i + 1}</div>
        ${avatarHtml(s.name, 44)}
        <div>
          <div class="lb-name">${s.name} ${s.is_dpiit_certified ? "· DPIIT demo-verified" : ""}</div>
          <div class="lb-tags">${s.tags.split(",").slice(0, 3).join(", ")} · ${s.state}</div>
        </div>
        ${riskBadgeHtml(s.risk_level)}
        <div class="lb-score">${s.score.toFixed(1)}</div>
      </div>
    `).join("");
    container.querySelectorAll(".lb-card").forEach(card => {
      card.addEventListener("click", () => showProfile(card.dataset.id));
    });
  } catch (e) {
    container.innerHTML = `<p class="empty-state">Could not reach the leaderboard service.</p>`;
  }
}

// ============================================================ Profile modal
async function showProfile(startupId) {
  const modalContent = document.getElementById("modalContent");
  modalContent.innerHTML = `<p class="empty-state">Loading profile…</p>`;
  openModal("profileModal");
  try {
    const p = await fetch(`${API_BASE}/api/startups/${startupId}/profile`).then(r => r.json());
    modalContent.innerHTML = `
      <div class="profile-header">
        ${avatarHtml(p.name, 56)}
        <div>
          <h2>${p.name}</h2>
          <span class="badge-verify ${p.verification_status}">${p.verification_status}</span>
          ${p.is_dpiit_certified ? '<span class="badge-verify verified">✓ DPIIT verified · demo source</span>' : '<span class="badge-verify">DPIIT not verified</span>'}
          ${p.is_women_led ? '<span class="badge-verify verified">Women-led</span>' : ""}
        </div>
      </div>
      <p style="font-size:13.5px; margin:14px 0;">${p.description || "No company description provided."}</p>
      <div class="match-meta">${p.sector || 'Unspecified sector'} · ${p.location || 'Location not provided'} · ${p.maturity_level || 'Maturity not provided'}</div>
      <h3 style="font-size:15px; margin-top:18px;">Capabilities</h3>
      <p style="font-size:13px; color:var(--ink-soft);">${p.capabilities || p.tags || '—'}</p>
      <h3 style="font-size:15px; margin-top:18px;">Past deployments</h3>
      <p style="font-size:13px;">${p.past_deployments || p.achievements || 'No deployments listed.'}</p>
      <div class="score-total" style="font-size:34px; margin-top:16px;">${p.score.toFixed(1)}<span class="score-total-label">/100 SETU Score</span></div>
      <div class="risk-line">Pilot risk: ${riskBadgeHtml(p.risk.risk_level)} <span style="color:var(--ink-soft);">(${p.risk.risk_score}/100)</span></div>
      <p style="font-size:12.5px; color:var(--ink-soft);">Verified evidence: ${p.verified_evidence_count || 0} · Past contracts: ${p.past_contracts}</p>
      <h3 style="font-size:15px; margin-top:20px;">Feedback history (${p.feedback_count})</h3>
      <div class="feedback-history">
        ${p.feedback_history.length ? p.feedback_history.map(f => `
          <div class="feedback-row"><span>${f.date}</span><span class="feedback-rating">${f.rating}/10</span></div>
        `).join("") : '<p class="empty-state">No pilots completed yet.</p>'}
      </div>
    `;
  } catch (e) {
    modalContent.innerHTML = `<p class="empty-state">Could not load this profile.</p>`;
  }
}

// ============================================================ Government: post problem -> AI match
document.getElementById("problemForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = document.getElementById("probTitle").value;
  const department = document.getElementById("probDept").value;
  const problem_context = document.getElementById("probContext").value;
  const desired_outcome = document.getElementById("probOutcome").value;
  const capabilities_needed = document.getElementById("probCapabilities").value;
  const skills_needed = document.getElementById("probSkills").value;
  const sector = document.getElementById("probSector").value;
  const kpis = document.getElementById("probKpi").value;
  const geography = document.getElementById("probGeography").value;
  const budget_lakh = parseFloat(document.getElementById("probBudget").value) || 25;

  const list = document.getElementById("matchList");
  list.innerHTML = `<li class="empty-state">Running AI matching against the register…</li>`;

  try {
    const res = await fetch(`${API_BASE}/api/match-startups`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, department, problem_context, desired_outcome, capabilities_needed, skills_needed, sector, kpis, geography, budget_lakh }),
    });
    const data = await res.json();
    renderMatches(data.matches);
  } catch (err) {
    list.innerHTML = `<li class="empty-state">Could not reach the matching service.</li>`;
  }
});

function renderMatches(matches) {
  const list = document.getElementById("matchList");
  document.getElementById("matchCount").textContent = `${matches.length} candidates`;
  if (!matches.length) {
    list.innerHTML = `<li class="empty-state">No relevant startups found in the current registry. Try refining the problem domain.</li>`;
    return;
  }
  list.innerHTML = matches.map(m => {
    const caps = (m.matched_capabilities || m.matched_terms || []).slice(0, 4);
    const terms = caps.map(t => `<mark>${t}</mark>`).join(" ");
    const verified = m.dpiit_status === "verified";
    const evidence = m.verified_evidence_count ?? 0;
    return `
      <li class="match-item semantic-match-card" data-id="${m.startup_id}">
        ${avatarHtml(m.name, 50)}
        <span class="match-main">
          <div class="match-name">${m.name} ${verified ? '<span class="badge-verify verified">✓ DPIIT verified · demo source</span>' : '<span class="badge-verify">DPIIT ' + (m.dpiit_status || 'unverified') + '</span>'}</div>
          <div class="match-meta">${m.sector || 'Unspecified sector'} · ${m.location || 'Location not provided'}</div>
          <div class="match-reason-title">Why this matched</div>
          <div class="match-terms">${terms || m.why_matched || 'Semantic similarity to the challenge'}</div>
          <div class="match-evidence">Verified evidence: ${evidence} · Past deployments: ${m.past_deployments_count || 0}</div>
        </span>
        <span class="match-right">
          <span class="match-score">${Number(m.match_score).toFixed(0)}% semantic fit</span>
          <span class="mini-score">SETU Score ${Number(m.setu_score ?? m.current_score ?? 0).toFixed(1)}</span>
          ${riskBadgeHtml(m.risk_level)}
        </span>
      </li>
    `;
  }).join("");
  list.querySelectorAll(".match-item").forEach(item => item.addEventListener("click", () => showProfile(item.dataset.id)));
}

// ============================================================ Startup: register / login
document.getElementById("showStartupLogin").addEventListener("click", () => {
  document.querySelector("#startupGuestView .form-panel").style.display = "none";
  document.getElementById("startupLoginPanel").style.display = "block";
});
document.getElementById("showStartupRegister").addEventListener("click", () => {
  document.getElementById("startupLoginPanel").style.display = "none";
  document.querySelector("#startupGuestView .form-panel").style.display = "block";
});

document.getElementById("startupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById("suName").value,
    email: document.getElementById("suEmail").value,
    password: document.getElementById("suPassword").value,
    tags: document.getElementById("suTags").value,
    achievements: document.getElementById("suAchievements").value,
    is_dpiit_certified: document.getElementById("suDpiit").checked,
    is_women_led: document.getElementById("suWomen").checked,
    state: document.getElementById("suState").value,
  };
  try {
    const res = await fetch(`${API_BASE}/api/auth/startup/register`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    if (!res.ok) { const err = await res.json(); alert(err.detail || "Registration failed"); return; }
    const data = await res.json();
    saveSession(data, "startup");
    renderStartupDeskState();
    loadStats();
  } catch (err) {
    alert("Could not reach the server.");
  }
});

document.getElementById("startupLoginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("suLoginEmail").value;
  const password = document.getElementById("suLoginPassword").value;
  try {
    const res = await fetch(`${API_BASE}/api/auth/startup/login`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }),
    });
    if (!res.ok) { const err = await res.json(); alert(err.detail || "Login failed"); return; }
    const data = await res.json();
    saveSession(data, "startup");
    renderStartupDeskState();
  } catch (err) {
    alert("Could not reach the server.");
  }
});

document.getElementById("govLoginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("govLoginEmail").value;
  const password = document.getElementById("govLoginPassword").value;
  try {
    const res = await fetch(`${API_BASE}/api/auth/gov/login`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }),
    });
    if (!res.ok) { const err = await res.json(); alert(err.detail || "Login failed"); return; }
    const data = await res.json();
    saveSession(data, "gov");
    closeModal("authModal");
    goToPage("gov");
  } catch (err) {
    alert("Could not reach the server.");
  }
});

async function renderStartupDeskState() {
  const guestView = document.getElementById("startupGuestView");
  const dashboard = document.getElementById("startupDashboard");
  if (session && session.type === "startup") {
    guestView.style.display = "none";
    dashboard.style.display = "block";
    try {
      const p = await fetch(`${API_BASE}/api/startups/${session.startup_id}/profile`).then(r => r.json());
      document.getElementById("ownAvatar").outerHTML = avatarHtml(p.name, 56);
      document.getElementById("ownName").textContent = p.name;
      const verifyEl = document.getElementById("ownVerify");
      verifyEl.textContent = p.verification_status;
      verifyEl.className = "badge-verify " + p.verification_status;
      document.getElementById("scoreTotal").textContent = p.score.toFixed(1);
      document.getElementById("ownRiskBadge").outerHTML = riskBadgeHtml(p.risk.risk_level);

      const scoreRes = await fetch(`${API_BASE}/api/startups/${session.startup_id}/score`).then(r => r.json());
      const b = scoreRes.breakdown;
      document.getElementById("scoreBars").innerHTML = `
        ${scoreBarHtml("Policy fit (40%)", b.policy_score)}
        ${scoreBarHtml("Profile strength (30%)", b.profile_score)}
        ${scoreBarHtml("Past feedback (30%)", b.feedback_score)}
      `;

      const historyEl = document.getElementById("ownFeedbackHistory");
      historyEl.innerHTML = p.feedback_history.length
        ? p.feedback_history.map(f => `<div class="feedback-row"><span>${f.date}</span><span class="feedback-rating">${f.rating}/10</span></div>`).join("")
        : `<p class="empty-state">No feedback recorded yet — this fills in after your first completed pilot.</p>`;
    } catch (e) { console.error(e); }
  } else {
    guestView.style.display = "grid";
    dashboard.style.display = "none";
  }
}

function scoreBarHtml(label, value) {
  return `
    <div class="score-bar-row">
      <div class="score-bar-label"><span>${label}</span><span>${value.toFixed(0)}/100</span></div>
      <div class="score-bar-track"><div class="score-bar-fill" style="width:${Math.min(value, 100)}%"></div></div>
    </div>
  `;
}

// ============================================================ Finance / Contracts
document.getElementById("contractForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    startup_id: parseInt(document.getElementById("cStartupId").value),
    problem_title: document.getElementById("cTitle").value,
    department: document.getElementById("cDept").value,
    budget_lakh: parseFloat(document.getElementById("cBudget").value),
  };
  try {
    const res = await fetch(`${API_BASE}/api/contracts`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const data = await res.json();
    alert(`Contract created — ID ${data.contract_id}. Use this ID to view milestones.`);
    document.getElementById("viewContractId").value = data.contract_id;
    loadContract(data.contract_id);
  } catch (err) {
    alert("Could not create contract.");
  }
});

document.getElementById("loadContractBtn").addEventListener("click", () => {
  const id = document.getElementById("viewContractId").value;
  if (id) loadContract(id);
});

async function loadContract(contractId) {
  const track = document.getElementById("milestoneTrack");
  track.innerHTML = `<p class="empty-state">Loading…</p>`;
  try {
    const data = await fetch(`${API_BASE}/api/contracts/${contractId}`).then(r => r.json());
    track.innerHTML = `<p style="font-size:13px; color:var(--ink-soft); margin-bottom:10px;">${data.problem_title} · ${data.department}</p>` +
      data.milestones.map(m => `
        <div class="milestone-row">
          <div class="milestone-num">${m.milestone_number}</div>
          <div class="milestone-scope">${m.scope}</div>
          <div class="milestone-funds">₹${m.funds_allocated}L</div>
          <button class="status-pill status-${m.status}" data-contract="${contractId}" data-num="${m.milestone_number}" data-status="${m.status}">${m.status.replace("_", " ")}</button>
        </div>
      `).join("");
    track.querySelectorAll(".status-pill").forEach(btn => btn.addEventListener("click", advanceMilestone));
  } catch (e) {
    track.innerHTML = `<p class="empty-state">Contract not found.</p>`;
  }
}

const STATUS_CYCLE = ["planned", "in_progress", "delivered", "paid"];
async function advanceMilestone(e) {
  const btn = e.target;
  const current = btn.dataset.status;
  const nextIndex = (STATUS_CYCLE.indexOf(current) + 1) % STATUS_CYCLE.length;
  const nextStatus = STATUS_CYCLE[nextIndex];
  try {
    await fetch(`${API_BASE}/api/contracts/${btn.dataset.contract}/milestone/${btn.dataset.num}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: nextStatus }),
    });
    loadContract(btn.dataset.contract);
  } catch (err) {
    alert("Could not update milestone.");
  }
}

// ============================================================ Feedback
document.getElementById("feedbackForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = {
    startup_id: parseInt(document.getElementById("fbStartupId").value),
    contract_id: document.getElementById("fbContractId").value ? parseInt(document.getElementById("fbContractId").value) : null,
    rating: parseFloat(document.getElementById("fbRating").value),
    comment: document.getElementById("fbComment").value,
  };
  try {
    const res = await fetch(`${API_BASE}/api/feedback`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
    });
    const data = await res.json();
    alert(`Feedback recorded. Updated score: ${data.updated_score}`);
    e.target.reset();
    document.getElementById("fbRating").value = "8.5";
  } catch (err) {
    alert("Could not submit feedback.");
  }
});

document.getElementById("loadFeedbackBtn").addEventListener("click", async () => {
  const id = document.getElementById("viewFbStartupId").value;
  const list = document.getElementById("feedbackHistoryList");
  if (!id) return;
  list.innerHTML = `<p class="empty-state">Loading…</p>`;
  try {
    const records = await fetch(`${API_BASE}/api/feedback/${id}`).then(r => r.json());
    list.innerHTML = records.length
      ? records.map(f => `<div class="feedback-row"><span>${f.date}</span><span class="feedback-rating">${f.rating}/10</span></div>`).join("")
      : `<p class="empty-state">No feedback recorded for this startup yet.</p>`;
  } catch (e) {
    list.innerHTML = `<p class="empty-state">Could not load feedback.</p>`;
  }
});

// ============================================================ Full Language System (English / Hindi / Marathi)
const I18N = {
  en: {
    skipLink: "Skip to main content", govOfIndia: "Government of Maharashtra Initiative",
    textSize: "Text size", highContrast: "High contrast",
    deptLine: "Skills, Employment, Entrepreneurship & Innovation Department",
    notSignedIn: "Not signed in", brandSub: "Startup Enabled Transparent Upgradation",
    navHome: "Home", navGov: "Government Desk", navStartup: "Startup Desk",
    navLeaderboard: "Leaderboard", navFinance: "Finance", navFeedback: "Feedback", signIn: "Sign in",
    eyebrow: "Problem Statement 26136 · Smart India Hackathon 2026",
    heroTitle: "One register connecting government challenges with verified startup solutions.",
    heroLede: "AI-matched recommendations, risk-scored profiles, a public leaderboard, milestone-based finance tracking, and feedback that keeps improving every match.",
    fileProblem: "File a problem statement", registerStartup: "Register your startup",
    statRegistered: "Registered startups", statTopScore: "Top score today", statStatus: "System status", checking: "checking…",
    announceLabel: "Announcements",
    announce1: "Water & Sanitation Department opens 3 new problem statements for pilot bidding.",
    announce2: "DPIIT eligibility relaxation now applies automatically at registration.",
    announce3: "Average milestone payment time improved to 21 days this quarter.",
    workflowTitle: "How SETU works", workflowSub: "A four-stage pipeline, each stage backed by its own module.",
    wf1Title: "AI matching & risk prediction",
    wf1Body: "The problem statement is read by the matching engine, which ranks registered startups by skill-fit and pairs each match with a live risk score — track record, profile strength, and compliance standing, not a black box.",
    wf2Title: "Verified startup database",
    wf2Body: "Every startup keeps a public profile — specialisation, achievements, DPIIT status, verification badge — that both the matching and scoring engines read from directly.",
    wf3Title: "Transparent scoring & leaderboard",
    wf3Body: "A weighted, explainable formula (policy fit, profile strength, past feedback) ranks every startup on a public leaderboard — no hidden criteria.",
    wf4Title: "Finance tracking & feedback loop",
    wf4Body: "Once a startup is selected, a 4-milestone contract tracks scope and funds through to payment. Feedback after completion flows straight back into that startup's score for the next match.",
    impactTitle: "Impact so far",
    impact1: "Avg. days to first payment", impact2: "Departments onboarded",
    impact3: "Milestone-tracked disbursal", impact4: "Turnover-clause rejections",
    deptsTitle: "Participating departments",
    deptTransport: "Urban Transport", deptHealth: "Public Health", deptWater: "Water & Sanitation",
    deptEdu: "Education", deptAgri: "Agriculture", deptInnovation: "Skills, Employment & Innovation",
    faqTitle: "Frequently asked questions",
    faq1q: "Who is eligible to register as a startup?",
    faq1a: "Any DPIIT-recognised startup, or one in the process of recognition, may register. DPIIT recognition removes the usual prior-turnover and past-experience requirements for pilot-stage engagements.",
    faq2q: "How is the match score calculated?",
    faq2a: "SETU uses semantic similarity across the complete challenge, then combines capability and sector relevance. The result also shows readable reasons and matched capabilities so an officer can inspect why a startup was surfaced.",
    faq3q: "What happens if a milestone is missed?",
    faq3a: "Funds for a milestone are only released once it is marked delivered and verified. A missed milestone simply withholds that tranche — it does not cancel earlier approved payments.",
    faq4q: "Is my startup's data secure?",
    faq4a: "Passwords are hashed and never stored in plain text, and every session uses a unique, expiring access token.",
    govDeskTitle: "Government Desk", govDeskSub: "File a problem statement to get AI-ranked, risk-scored startup recommendations.",
    fileProblemTitle: "File a problem statement", labelTitle: "Title", labelDept: "Department",
    labelSkills: "Skills / domain needed", labelBudget: "Pilot budget ceiling (₹ lakh)",
    getRecommendations: "Get AI recommendations", rankedMatches: "AI-ranked matches",
    matchEmpty: "File a problem statement to see AI-matched, risk-scored startups here.",
    startupDeskTitle: "Startup Desk", startupDeskSub: "Register your profile, track your live score, and see how it's calculated.",
    registerTitle: "Register your startup", labelStartupName: "Startup name", labelEmail: "Email",
    labelPassword: "Password", labelTags: "Specialisation / tags", hintCommaSep: "(comma separated)",
    labelAchievements: "Achievements / past work", dpiitCert: "DPIIT recognised", womenLed: "Women-led",
    labelState: "State", registerBtn: "Register", alreadyRegistered: "Already registered?",
    signInInstead: "Sign in instead", signInTitle: "Sign in to your startup account", demoLogin: "Demo login:",
    newHere: "New here?", registerInstead: "Register instead", pilotRisk: "Pilot risk:",
    feedbackHistoryTitle: "Feedback history", noFeedbackYet: "No feedback recorded yet — this fills in after your first completed pilot.",
    leaderboardTitle: "Statewide Leaderboard",
    leaderboardSub: "Score = policy fit (40%) + profile strength (30%) + past feedback (30%). Fully explainable — click any startup to see its full profile.",
    financeTitle: "Finance Management", financeSub: "Milestone-based contract tracking — no funds move until a milestone is marked delivered.",
    createContract: "Create a pilot contract", labelStartupId: "Startup ID", labelProblemTitle: "Problem title",
    labelDeptText: "Department", labelTotalBudget: "Total budget (₹ lakh)", createContractBtn: "Create contract",
    viewContract: "View contract", labelContractId: "Contract ID", loadMilestones: "Load milestones",
    feedbackPageTitle: "Feedback for Future Matching", feedbackPageSub: "Feedback submitted here updates the startup's score immediately, improving future AI recommendations.",
    submitFeedback: "Submit feedback", labelContractIdOpt: "Contract ID", hintOptional: "(optional)",
    labelRating: "Rating", hintOutOf10: "(out of 10)", labelComment: "Comment", submitFeedbackBtn: "Submit feedback",
    viewFeedbackHistory: "View feedback history", loadHistory: "Load history",
    signInTitle2: "Sign in", chooseDesk: "Choose which desk you're signing in to.",
    startupSignIn: "Startup sign in", govSignIn: "Government sign in",
    footerText: "Smart India Hackathon 2026, Problem Statement 26136. All data on this page is read from and written to live backend modules via core-apis.",
    footerContact: "Contact", footerLinks: "Quick links",
  },

  hi: {
    skipLink: "मुख्य सामग्री पर जाएँ", govOfIndia: "महाराष्ट्र सरकार की पहल",
    textSize: "टेक्स्ट आकार", highContrast: "उच्च कंट्रास्ट",
    deptLine: "कौशल्य, रोजगार, उद्योजकता व नवोन्मेष विभाग",
    notSignedIn: "साइन इन नहीं है", brandSub: "स्टार्टअप सक्षम पारदर्शी उन्नयन",
    navHome: "होम", navGov: "सरकारी डेस्क", navStartup: "स्टार्टअप डेस्क",
    navLeaderboard: "लीडरबोर्ड", navFinance: "वित्त प्रबंधन", navFeedback: "प्रतिक्रिया", signIn: "साइन इन करें",
    eyebrow: "समस्या विवरण 26136 · स्मार्ट इंडिया हैकाथॉन 2026",
    heroTitle: "एक ऐसा रजिस्टर जो सरकारी समस्याओं को सत्यापित स्टार्टअप समाधानों से जोड़ता है।",
    heroLede: "एआई-आधारित सिफारिशें, जोखिम-स्कोर वाली प्रोफ़ाइलें, सार्वजनिक लीडरबोर्ड, माइलस्टोन-आधारित वित्तीय ट्रैकिंग, और ऐसी प्रतिक्रिया जो हर मिलान को बेहतर बनाती रहती है।",
    fileProblem: "समस्या विवरण दर्ज करें", registerStartup: "अपना स्टार्टअप पंजीकृत करें",
    statRegistered: "पंजीकृत स्टार्टअप", statTopScore: "आज का सर्वोच्च स्कोर", statStatus: "सिस्टम स्थिति", checking: "जाँच हो रही है…",
    announceLabel: "घोषणाएँ",
    announce1: "जल एवं स्वच्छता विभाग ने पायलट बोली के लिए 3 नए समस्या विवरण जारी किए।",
    announce2: "पंजीकरण के समय अब DPIIT पात्रता में छूट स्वतः लागू होती है।",
    announce3: "इस तिमाही औसत माइलस्टोन भुगतान समय सुधरकर 21 दिन हुआ।",
    workflowTitle: "SETU कैसे काम करता है", workflowSub: "चार चरणों की प्रक्रिया, हर चरण अपने अलग मॉड्यूल पर आधारित है।",
    wf1Title: "एआई मिलान और जोखिम पूर्वानुमान",
    wf1Body: "समस्या विवरण को मिलान इंजन पढ़ता है, जो पंजीकृत स्टार्टअप को कौशल-अनुकूलता के आधार पर रैंक करता है और हर मिलान के साथ एक लाइव जोखिम स्कोर जोड़ता है — ट्रैक रिकॉर्ड, प्रोफ़ाइल मजबूती और अनुपालन स्थिति, कोई छिपा हुआ मॉडल नहीं।",
    wf2Title: "सत्यापित स्टार्टअप डेटाबेस",
    wf2Body: "हर स्टार्टअप की एक सार्वजनिक प्रोफ़ाइल होती है — विशेषज्ञता, उपलब्धियाँ, DPIIT स्थिति, सत्यापन बैज — जिसे मिलान और स्कोरिंग दोनों इंजन सीधे पढ़ते हैं।",
    wf3Title: "पारदर्शी स्कोरिंग और लीडरबोर्ड",
    wf3Body: "एक भारित, स्पष्ट सूत्र (नीति-अनुकूलता, प्रोफ़ाइल मजबूती, पिछली प्रतिक्रिया) हर स्टार्टअप को सार्वजनिक लीडरबोर्ड पर रैंक करता है — कोई छिपा मापदंड नहीं।",
    wf4Title: "वित्त ट्रैकिंग और प्रतिक्रिया चक्र",
    wf4Body: "स्टार्टअप चुने जाने के बाद, 4-माइलस्टोन अनुबंध कार्यक्षेत्र और धनराशि को भुगतान तक ट्रैक करता है। पूर्ण होने के बाद की प्रतिक्रिया सीधे उस स्टार्टअप के स्कोर में जुड़ जाती है, अगले मिलान के लिए।",
    impactTitle: "अब तक का प्रभाव",
    impact1: "पहले भुगतान तक औसत दिन", impact2: "जुड़े हुए विभाग",
    impact3: "माइलस्टोन-ट्रैक्ड संवितरण", impact4: "टर्नओवर-शर्त अस्वीकृतियाँ",
    deptsTitle: "सहभागी विभाग",
    deptTransport: "शहरी परिवहन", deptHealth: "सार्वजनिक स्वास्थ्य", deptWater: "जल एवं स्वच्छता",
    deptEdu: "शिक्षा", deptAgri: "कृषि", deptInnovation: "कौशल्य, रोजगार व नवोन्मेष",
    faqTitle: "अक्सर पूछे जाने वाले प्रश्न",
    faq1q: "स्टार्टअप के रूप में पंजीकरण के लिए कौन पात्र है?",
    faq1a: "कोई भी DPIIT-मान्यता प्राप्त स्टार्टअप, या मान्यता प्रक्रिया में मौजूद स्टार्टअप, पंजीकरण कर सकता है। DPIIT मान्यता पायलट-चरण जुड़ाव के लिए सामान्य पूर्व-टर्नओवर और पूर्व-अनुभव आवश्यकताओं को हटा देती है।",
    faq2q: "मिलान स्कोर की गणना कैसे होती है?",
    faq2a: "मिलान इंजन समस्या विवरण में आवश्यक कौशलों की तुलना हर स्टार्टअप के घोषित टैग से करता है। यह एक पारदर्शी ओवरलैप स्कोर है, कोई छिपा हुआ मॉडल नहीं — आप देख सकते हैं कि वास्तव में कौन-से शब्द मेल खाए।",
    faq3q: "यदि कोई माइलस्टोन छूट जाए तो क्या होगा?",
    faq3a: "किसी माइलस्टोन की धनराशि तभी जारी होती है जब उसे पूर्ण और सत्यापित चिह्नित किया जाता है। छूटा हुआ माइलस्टोन केवल उस किश्त को रोकता है — यह पहले से स्वीकृत भुगतानों को रद्द नहीं करता।",
    faq4q: "क्या मेरे स्टार्टअप का डेटा सुरक्षित है?",
    faq4a: "पासवर्ड हैश किए जाते हैं और कभी भी सादे टेक्स्ट में संग्रहीत नहीं होते, और हर सत्र एक अद्वितीय, समयबद्ध एक्सेस टोकन का उपयोग करता है।",
    govDeskTitle: "सरकारी डेस्क", govDeskSub: "एआई-रैंक्ड, जोखिम-स्कोर वाली स्टार्टअप सिफारिशें पाने के लिए समस्या विवरण दर्ज करें।",
    fileProblemTitle: "समस्या विवरण दर्ज करें", labelTitle: "शीर्षक", labelDept: "विभाग",
    labelSkills: "आवश्यक कौशल / क्षेत्र", labelBudget: "पायलट बजट सीमा (₹ लाख)",
    getRecommendations: "एआई सिफारिशें प्राप्त करें", rankedMatches: "एआई-रैंक्ड मिलान",
    matchEmpty: "एआई-मिलान वाले, जोखिम-स्कोर किए गए स्टार्टअप देखने के लिए एक समस्या विवरण दर्ज करें।",
    startupDeskTitle: "स्टार्टअप डेस्क", startupDeskSub: "अपनी प्रोफ़ाइल पंजीकृत करें, अपना लाइव स्कोर देखें, और जानें यह कैसे गणना होता है।",
    registerTitle: "अपना स्टार्टअप पंजीकृत करें", labelStartupName: "स्टार्टअप का नाम", labelEmail: "ईमेल",
    labelPassword: "पासवर्ड", labelTags: "विशेषज्ञता / टैग", hintCommaSep: "(अल्पविराम से अलग करें)",
    labelAchievements: "उपलब्धियाँ / पिछला कार्य", dpiitCert: "DPIIT मान्यता प्राप्त", womenLed: "महिला-नेतृत्व वाला",
    labelState: "राज्य", registerBtn: "पंजीकरण करें", alreadyRegistered: "पहले से पंजीकृत हैं?",
    signInInstead: "इसके बजाय साइन इन करें", signInTitle: "अपने स्टार्टअप खाते में साइन इन करें", demoLogin: "डेमो लॉगिन:",
    newHere: "नए हैं?", registerInstead: "इसके बजाय पंजीकरण करें", pilotRisk: "पायलट जोखिम:",
    feedbackHistoryTitle: "प्रतिक्रिया इतिहास", noFeedbackYet: "अभी तक कोई प्रतिक्रिया दर्ज नहीं हुई — यह आपके पहले पूर्ण पायलट के बाद भरेगा।",
    leaderboardTitle: "राज्यव्यापी लीडरबोर्ड",
    leaderboardSub: "स्कोर = नीति-अनुकूलता (40%) + प्रोफ़ाइल मजबूती (30%) + पिछली प्रतिक्रिया (30%)। पूरी तरह स्पष्ट — पूर्ण प्रोफ़ाइल देखने के लिए किसी भी स्टार्टअप पर क्लिक करें।",
    financeTitle: "वित्त प्रबंधन", financeSub: "माइलस्टोन-आधारित अनुबंध ट्रैकिंग — जब तक माइलस्टोन पूर्ण चिह्नित न हो, कोई धनराशि जारी नहीं होती।",
    createContract: "पायलट अनुबंध बनाएँ", labelStartupId: "स्टार्टअप आईडी", labelProblemTitle: "समस्या शीर्षक",
    labelDeptText: "विभाग", labelTotalBudget: "कुल बजट (₹ लाख)", createContractBtn: "अनुबंध बनाएँ",
    viewContract: "अनुबंध देखें", labelContractId: "अनुबंध आईडी", loadMilestones: "माइलस्टोन लोड करें",
    feedbackPageTitle: "भविष्य के मिलान के लिए प्रतिक्रिया", feedbackPageSub: "यहाँ दी गई प्रतिक्रिया तुरंत स्टार्टअप का स्कोर अपडेट करती है, जिससे भविष्य की एआई सिफारिशें बेहतर होती हैं।",
    submitFeedback: "प्रतिक्रिया सबमिट करें", labelContractIdOpt: "अनुबंध आईडी", hintOptional: "(वैकल्पिक)",
    labelRating: "रेटिंग", hintOutOf10: "(10 में से)", labelComment: "टिप्पणी", submitFeedbackBtn: "प्रतिक्रिया सबमिट करें",
    viewFeedbackHistory: "प्रतिक्रिया इतिहास देखें", loadHistory: "इतिहास लोड करें",
    signInTitle2: "साइन इन करें", chooseDesk: "चुनें कि आप किस डेस्क में साइन इन कर रहे हैं।",
    startupSignIn: "स्टार्टअप साइन इन", govSignIn: "सरकारी साइन इन",
    footerText: "स्मार्ट इंडिया हैकाथॉन 2026, समस्या विवरण 26136। इस पृष्ठ का सारा डेटा core-apis के माध्यम से लाइव बैकएंड मॉड्यूल से पढ़ा और लिखा जाता है।",
    footerContact: "संपर्क", footerLinks: "त्वरित लिंक",
  },

  mr: {
    skipLink: "मुख्य मजकुराकडे जा", govOfIndia: "महाराष्ट्र शासनाचा उपक्रम",
    textSize: "मजकूर आकार", highContrast: "उच्च कॉन्ट्रास्ट",
    deptLine: "कौशल्य, रोजगार, उद्योजकता व नाविन्यता विभाग",
    notSignedIn: "साइन इन केलेले नाही", brandSub: "स्टार्टअप सक्षम पारदर्शी उन्नयन",
    navHome: "मुख्यपृष्ठ", navGov: "शासकीय डेस्क", navStartup: "स्टार्टअप डेस्क",
    navLeaderboard: "लीडरबोर्ड", navFinance: "वित्त व्यवस्थापन", navFeedback: "प्रतिक्रिया", signIn: "साइन इन करा",
    eyebrow: "समस्या विवरण 26136 · स्मार्ट इंडिया हॅकाथॉन 2026",
    heroTitle: "एक नोंदणी जी सरकारी आव्हानांना पडताळणी केलेल्या स्टार्टअप उपायांशी जोडते.",
    heroLede: "एआय-जुळणी शिफारसी, जोखीम-गुण असलेल्या प्रोफाइल्स, सार्वजनिक लीडरबोर्ड, टप्पानिहाय आर्थिक ट्रॅकिंग, आणि प्रत्येक जुळणी सुधारणारी प्रतिक्रिया.",
    fileProblem: "समस्या विवरण सादर करा", registerStartup: "आपला स्टार्टअप नोंदवा",
    statRegistered: "नोंदणीकृत स्टार्टअप्स", statTopScore: "आजचा सर्वोच्च गुण", statStatus: "प्रणाली स्थिती", checking: "तपासत आहे…",
    announceLabel: "घोषणा",
    announce1: "जल व स्वच्छता विभागाने पायलट निविदेसाठी 3 नवीन समस्या विवरणे जाहीर केली.",
    announce2: "नोंदणीच्या वेळी आता DPIIT पात्रता सवलत आपोआप लागू होते.",
    announce3: "या तिमाहीत सरासरी टप्पा-पेमेंट वेळ सुधारून 21 दिवस झाला.",
    workflowTitle: "SETU कसे कार्य करते", workflowSub: "चार टप्प्यांची प्रक्रिया, प्रत्येक टप्पा स्वतंत्र मॉड्यूलवर आधारित.",
    wf1Title: "एआय जुळणी व जोखीम अंदाज",
    wf1Body: "समस्या विवरण जुळणी इंजिन वाचते, जे नोंदणीकृत स्टार्टअप्सना कौशल्य-अनुकूलतेनुसार क्रमवारी लावते आणि प्रत्येक जुळणीसोबत थेट जोखीम गुण देते — ट्रॅक रेकॉर्ड, प्रोफाइल मजबुती व अनुपालन स्थिती, कोणतेही लपलेले मॉडेल नाही.",
    wf2Title: "पडताळणी केलेला स्टार्टअप डेटाबेस",
    wf2Body: "प्रत्येक स्टार्टअपची सार्वजनिक प्रोफाइल असते — विशेषज्ञता, कामगिरी, DPIIT स्थिती, पडताळणी बॅज — जी जुळणी व गुणांकन दोन्ही इंजिन थेट वाचतात.",
    wf3Title: "पारदर्शक गुणांकन व लीडरबोर्ड",
    wf3Body: "भारित, स्पष्ट सूत्र (धोरण-अनुकूलता, प्रोफाइल मजबुती, मागील प्रतिक्रिया) प्रत्येक स्टार्टअपला सार्वजनिक लीडरबोर्डवर क्रमवारी देते — कोणतेही लपलेले निकष नाहीत.",
    wf4Title: "आर्थिक ट्रॅकिंग व प्रतिक्रिया चक्र",
    wf4Body: "स्टार्टअप निवडल्यानंतर, 4-टप्प्यांचा करार व्याप्ती व निधी पेमेंटपर्यंत ट्रॅक करतो. पूर्ण झाल्यानंतरची प्रतिक्रिया थेट त्या स्टार्टअपच्या गुणांमध्ये पुढील जुळणीसाठी जोडली जाते.",
    impactTitle: "आत्तापर्यंतचा प्रभाव",
    impact1: "पहिल्या पेमेंटपर्यंत सरासरी दिवस", impact2: "सामील झालेले विभाग",
    impact3: "टप्पा-ट्रॅक्ड वितरण", impact4: "उलाढाल-अट नकार",
    deptsTitle: "सहभागी विभाग",
    deptTransport: "शहरी वाहतूक", deptHealth: "सार्वजनिक आरोग्य", deptWater: "जल व स्वच्छता",
    deptEdu: "शिक्षण", deptAgri: "कृषी", deptInnovation: "कौशल्य, रोजगार व नाविन्यता",
    faqTitle: "वारंवार विचारले जाणारे प्रश्न",
    faq1q: "स्टार्टअप म्हणून नोंदणीसाठी कोण पात्र आहे?",
    faq1a: "कोणताही DPIIT-मान्यताप्राप्त स्टार्टअप, किंवा मान्यता प्रक्रियेत असलेला स्टार्टअप, नोंदणी करू शकतो. DPIIT मान्यता पायलट-टप्प्यातील सहभागासाठी नेहमीच्या पूर्व-उलाढाल व पूर्व-अनुभव अटी काढून टाकते.",
    faq2q: "जुळणी गुण कसे मोजले जातात?",
    faq2a: "जुळणी इंजिन समस्या विवरणाला आवश्यक कौशल्यांची तुलना प्रत्येक स्टार्टअपच्या नमूद टॅगशी करते. हा एक पारदर्शक ओव्हरलॅप गुण आहे, लपलेले मॉडेल नाही — कोणते शब्द जुळले हे तुम्ही पाहू शकता.",
    faq3q: "टप्पा चुकल्यास काय होते?",
    faq3a: "टप्प्याचा निधी तो पूर्ण व पडताळणी झाल्याचे चिन्हांकित केल्यावरच जारी होतो. चुकलेला टप्पा फक्त तो हप्ता रोखतो — आधी मंजूर झालेले पेमेंट रद्द करत नाही.",
    faq4q: "माझ्या स्टार्टअपचा डेटा सुरक्षित आहे का?",
    faq4a: "पासवर्ड्स हॅश केले जातात आणि कधीही साध्या मजकुरात साठवले जात नाहीत, आणि प्रत्येक सत्र एक अद्वितीय, मुदत संपणारा अ‍ॅक्सेस टोकन वापरते.",
    govDeskTitle: "शासकीय डेस्क", govDeskSub: "एआय-क्रमवारी, जोखीम-गुण असलेल्या स्टार्टअप शिफारसींसाठी समस्या विवरण सादर करा.",
    fileProblemTitle: "समस्या विवरण सादर करा", labelTitle: "शीर्षक", labelDept: "विभाग",
    labelSkills: "आवश्यक कौशल्ये / क्षेत्र", labelBudget: "पायलट अंदाजपत्रक मर्यादा (₹ लाख)",
    getRecommendations: "एआय शिफारसी मिळवा", rankedMatches: "एआय-क्रमवारी जुळण्या",
    matchEmpty: "एआय-जुळणी व जोखीम-गुण असलेले स्टार्टअप्स पाहण्यासाठी समस्या विवरण सादर करा.",
    startupDeskTitle: "स्टार्टअप डेस्क", startupDeskSub: "आपली प्रोफाइल नोंदवा, थेट गुण पाहा, आणि तो कसा मोजला जातो ते समजून घ्या.",
    registerTitle: "आपला स्टार्टअप नोंदवा", labelStartupName: "स्टार्टअपचे नाव", labelEmail: "ईमेल",
    labelPassword: "पासवर्ड", labelTags: "विशेषज्ञता / टॅग्स", hintCommaSep: "(स्वल्पविरामाने वेगळे करा)",
    labelAchievements: "कामगिरी / मागील काम", dpiitCert: "DPIIT मान्यताप्राप्त", womenLed: "महिला-नेतृत्वाखालील",
    labelState: "राज्य", registerBtn: "नोंदणी करा", alreadyRegistered: "आधीच नोंदणीकृत आहात?",
    signInInstead: "त्याऐवजी साइन इन करा", signInTitle: "आपल्या स्टार्टअप खात्यात साइन इन करा", demoLogin: "डेमो लॉगिन:",
    newHere: "नवीन आहात?", registerInstead: "त्याऐवजी नोंदणी करा", pilotRisk: "पायलट जोखीम:",
    feedbackHistoryTitle: "प्रतिक्रिया इतिहास", noFeedbackYet: "अद्याप कोणतीही प्रतिक्रिया नोंदवली नाही — तुमचा पहिला पूर्ण पायलट झाल्यावर हे भरेल.",
    leaderboardTitle: "राज्यव्यापी लीडरबोर्ड",
    leaderboardSub: "गुण = धोरण-अनुकूलता (40%) + प्रोफाइल मजबुती (30%) + मागील प्रतिक्रिया (30%). पूर्णपणे स्पष्ट — संपूर्ण प्रोफाइल पाहण्यासाठी कोणत्याही स्टार्टअपवर क्लिक करा.",
    financeTitle: "वित्त व्यवस्थापन", financeSub: "टप्पानिहाय करार ट्रॅकिंग — टप्पा पूर्ण चिन्हांकित होईपर्यंत निधी हलत नाही.",
    createContract: "पायलट करार तयार करा", labelStartupId: "स्टार्टअप आयडी", labelProblemTitle: "समस्या शीर्षक",
    labelDeptText: "विभाग", labelTotalBudget: "एकूण अंदाजपत्रक (₹ लाख)", createContractBtn: "करार तयार करा",
    viewContract: "करार पाहा", labelContractId: "करार आयडी", loadMilestones: "टप्पे लोड करा",
    feedbackPageTitle: "भविष्यातील जुळणीसाठी प्रतिक्रिया", feedbackPageSub: "येथे दिलेली प्रतिक्रिया लगेच स्टार्टअपचा गुण अद्ययावत करते, ज्यामुळे भविष्यातील एआय शिफारसी सुधारतात.",
    submitFeedback: "प्रतिक्रिया सादर करा", labelContractIdOpt: "करार आयडी", hintOptional: "(पर्यायी)",
    labelRating: "रेटिंग", hintOutOf10: "(10 पैकी)", labelComment: "टिप्पणी", submitFeedbackBtn: "प्रतिक्रिया सादर करा",
    viewFeedbackHistory: "प्रतिक्रिया इतिहास पाहा", loadHistory: "इतिहास लोड करा",
    signInTitle2: "साइन इन करा", chooseDesk: "आपण कोणत्या डेस्कवर साइन इन करत आहात ते निवडा.",
    startupSignIn: "स्टार्टअप साइन इन", govSignIn: "शासकीय साइन इन",
    footerText: "स्मार्ट इंडिया हॅकाथॉन 2026, समस्या विवरण 26136. या पानावरील सर्व डेटा core-apis मार्फत थेट बॅकएंड मॉड्यूल्समधून वाचला व लिहिला जातो.",
    footerContact: "संपर्क", footerLinks: "जलद दुवे",
  },
};

function setI18nText(el, text) {
  if (el.children.length === 0) {
    el.textContent = text;
    return;
  }
  const textNode = Array.from(el.childNodes).find(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim().length > 0);
  if (textNode) {
    textNode.textContent = text + " ";
  } else {
    el.insertBefore(document.createTextNode(text + " "), el.firstChild);
  }
}

function applyLanguage(lang) {
  const dict = I18N[lang] || I18N.en;
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) setI18nText(el, dict[key]);
  });
  document.getElementById("htmlRoot").lang = lang;
  localStorage.setItem("setu_lang", lang);
}

document.getElementById("langSwitch").addEventListener("change", (e) => applyLanguage(e.target.value));
const savedLang = localStorage.getItem("setu_lang") || "en";
document.getElementById("langSwitch").value = savedLang;
applyLanguage(savedLang);

// ============================================================ Accessibility: font size + contrast
let fontScale = parseFloat(localStorage.getItem("setu_font_scale") || "1");
function applyFontScale() {
  document.documentElement.style.setProperty("--font-scale", fontScale);
  localStorage.setItem("setu_font_scale", fontScale);
}
applyFontScale();
document.getElementById("fontIncrease").addEventListener("click", () => { fontScale = Math.min(1.3, fontScale + 0.1); applyFontScale(); });
document.getElementById("fontDecrease").addEventListener("click", () => { fontScale = Math.max(0.85, fontScale - 0.1); applyFontScale(); });
document.getElementById("fontReset").addEventListener("click", () => { fontScale = 1; applyFontScale(); });

if (localStorage.getItem("setu_contrast") === "on") document.body.classList.add("high-contrast");
document.getElementById("contrastToggle").addEventListener("click", () => {
  document.body.classList.toggle("high-contrast");
  localStorage.setItem("setu_contrast", document.body.classList.contains("high-contrast") ? "on" : "off");
});

document.getElementById("todayDate").textContent = new Date().toLocaleDateString(undefined, { day: "2-digit", month: "short", year: "numeric" });

// ============================================================ Init
renderSessionLabel();
renderStartupDeskState();
loadStats();
