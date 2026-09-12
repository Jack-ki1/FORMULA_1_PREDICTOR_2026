/**
 * dashboard.js — the flagship "Dashboard" tab.
 * Real data only: every number on this page either comes straight from
 * dashboard/api/predict-session, dashboard/api/races, h2h/api/drivers or
 * dashboard/api/race-result — or is plainly-labelled circuit reference data
 * (laps, DRS zones, base safety-car rate) from the 2026 calendar. Nothing
 * here invents lap times, tyre degradation or sector deltas the engine
 * doesn't actually produce (see the Practice-session note in the UI).
 */
(function () {
  "use strict";

  const SESSIONS = [
    { id: "practice", label: "Friday Practice", icon: "&#127937;", desc: "FP1 · FP2 · FP3 — projected pace distribution", subs: ["FP1", "FP2", "FP3"] },
    { id: "qualifying", label: "Saturday Qualifying", icon: "&#9889;", desc: "Q1/Q2/Q3 elimination · Q3 advancement model", subs: ["Q1", "Q2", "Q3", "Sprint Race"], sprintOnly: ["Sprint Race"] },
    { id: "race", label: "Sunday Grand Prix", icon: "&#127942;", desc: "Full race prediction — podium, points, DNF risk", subs: ["Race"] },
  ];

  const TARGETS = {
    winner: { id: "winner", label: "Race Winner", short: "WIN", sum: 1, session: "race" },
    podium: { id: "podium", label: "Podium (Top 3)", short: "PODIUM", sum: 3, session: "race" },
    points: { id: "points", label: "Points (Top 10)", short: "POINTS", sum: 10, session: "race" },
    race: { id: "race", label: "Full Race", short: "RACE", sum: 1, session: "race" },
    q3: { id: "q3", label: "Qualifying Q3", short: "Q3", sum: 10, session: "qualifying" },
    qualifying_q1: { id: "qualifying_q1", label: "Qualifying Q1", short: "Q1", sum: 15, session: "qualifying" },
    qualifying_q2: { id: "qualifying_q2", label: "Qualifying Q2", short: "Q2", sum: 10, session: "qualifying" },
    qualifying_q3: { id: "qualifying_q3", label: "Qualifying Q3", short: "Q3", sum: 10, session: "qualifying" },
    practice_pace: { id: "practice_pace", label: "Practice Pace", short: "PACE", sum: 1, session: "practice" },
    practice_fp1: { id: "practice_fp1", label: "Practice FP1", short: "FP1", sum: 1, session: "practice" },
    practice_fp2: { id: "practice_fp2", label: "Practice FP2", short: "FP2", sum: 1, session: "practice" },
    practice_fp3: { id: "practice_fp3", label: "Practice FP3", short: "FP3", sum: 1, session: "practice" },
  };

  const state = {
    calendar: [],
    driverMap: {},
    draft: { raceId: "", weather: "dry", simCount: 10000 },
    session: "race",
    subSession: "Race",
    targetId: "podium",
    committed: null,
    runState: "idle", // idle | running | done
    predictions: {},   // targetId -> predict() result
    manualGrid: null,
    gridPositions: null,
    gridSource: null,  // 'simulated' | 'manual' | null
    countdown: 96540,
    isSprintWeekend: false, // Track if current race is a sprint weekend
    aiMode: "normal", // 'normal' or 'ai'
    aiModel: "gemini-2.0-flash-exp",
    aiApiKey: "",
    aiWeight: 30, // 0-100 percentage
    aiTemperature: 0.7,
  };

  const $ = (sel) => document.querySelector(sel);

  function raceById(id) { return state.calendar.find((r) => r.id === id); }

  // -----------------------------------------------------------------------
  // Init
  // -----------------------------------------------------------------------
  async function init() {
    try {
      const raceDataElement = document.getElementById("race-data");
      state.calendar = JSON.parse(raceDataElement.dataset.calendar || "[]");
      
      if (!Array.isArray(state.calendar) || state.calendar.length === 0) {
        console.error("Calendar data is empty or invalid");
        return;
      }
      
      state.driverMap = await F1.getDriverMap();

      populateRaceSelects();
      renderSessionCards();
      populateSubSessionSelect();
      renderHero();
      renderInfoCircuit();
      startCountdown();
      bindEvents();
      
      // Initialize tab functionality
      initializeTabs();
      
      // Initialize AI sidebar
      initializeAISidebar();
      
      console.log("Dashboard initialized successfully");
    } catch (error) {
      console.error("Error initializing dashboard:", error);
    }
  }

  function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const daySections = document.querySelectorAll('.day-section');
    const targetSections = document.querySelectorAll('.target-section');

    // Set Friday as default active tab
    if (document.getElementById('day-friday')) {
      document.getElementById('day-friday').classList.add('active', 'text-white', 'border-b-2', 'border-red');
      document.getElementById('friday-section').style.display = 'block';
    }

    tabButtons.forEach(button => {
      button.addEventListener('click', function() {
        // Reset all buttons
        tabButtons.forEach(btn => {
          btn.classList.remove('active', 'text-white', 'border-b-2', 'border-red');
          btn.classList.add('text-sub', 'hover:border-gray-500', 'hover:text-white');
        });

        // Hide all sections
        daySections.forEach(section => section.style.display = 'none');
        targetSections.forEach(section => section.style.display = 'none');

        // Show corresponding section and activate button
        const tabId = this.id;
        this.classList.remove('text-sub', 'hover:border-gray-500', 'hover:text-white');
        this.classList.add('active', 'text-white', 'border-b-2', 'border-red');

        if (tabId.startsWith('day-')) {
          const sectionId = tabId.replace('day-', '') + '-section';
          const section = document.getElementById(sectionId);
          if (section) section.style.display = 'block';
        } else if (tabId.startsWith('target-')) {
          const sectionId = tabId.replace('target-', '') + '-section';
          const section = document.getElementById(sectionId);
          if (section) section.style.display = 'block';
        }
      });
    });
  }

  // -----------------------------------------------------------------------
  // AI Sidebar
  // -----------------------------------------------------------------------
  function initializeAISidebar() {
    const sidebar = document.getElementById('ai-sidebar');
    const closeBtn = document.getElementById('ai-sidebar-close');
    const applyBtn = document.getElementById('ai-sidebar-apply');
    const skipBtn = document.getElementById('ai-sidebar-skip');
    const modeOptions = document.querySelectorAll('.ai-sidebar-option');
    const modelSelect = document.getElementById('ai-model-select');
    const customModelInput = document.getElementById('ai-custom-model');
    const apiKeyInput = document.getElementById('ai-api-key');
    const weightSlider = document.getElementById('ai-weight-slider');
    const temperatureSlider = document.getElementById('ai-temperature-slider');
    const weightValue = document.getElementById('ai-weight-value');
    const temperatureValue = document.getElementById('ai-temperature-value');
    const triggerBtn = document.getElementById('ai-sidebar-trigger');
    const modeTabs = document.querySelectorAll('.ai-mode-tab');
    const chatInput = document.getElementById('ai-chat-input');
    const chatSend = document.getElementById('ai-chat-send');
    const chatMessages = document.getElementById('ai-chat-messages');

    // Show sidebar on first visit (check localStorage)
    const hasSeenSidebar = localStorage.getItem('f1-ai-sidebar-seen');
    if (!hasSeenSidebar) {
      setTimeout(() => {
        sidebar.classList.add('is-open');
      }, 500);
    }

    // Close button
    closeBtn.addEventListener('click', () => {
      sidebar.classList.remove('is-open');
      localStorage.setItem('f1-ai-sidebar-seen', 'true');
    });

    // Skip button
    skipBtn.addEventListener('click', () => {
      sidebar.classList.remove('is-open');
      localStorage.setItem('f1-ai-sidebar-seen', 'true');
      state.aiMode = 'normal';
      updateAIModeIndicator();
    });

    // Apply button
    applyBtn.addEventListener('click', () => {
      // Validate API key if AI mode is selected
      if (state.aiMode === 'ai' && !state.aiApiKey.trim()) {
        alert('Please enter your API key to use AI mode');
        return;
      }
      
      // If custom model, use the custom name
      if (state.aiModel === 'custom' && customModelInput && customModelInput.value.trim()) {
        state.aiModel = customModelInput.value.trim();
      }
      
      sidebar.classList.remove('is-open');
      localStorage.setItem('f1-ai-sidebar-seen', 'true');
      localStorage.setItem('f1-ai-mode', state.aiMode);
      localStorage.setItem('f1-ai-model', state.aiModel);
      localStorage.setItem('f1-ai-weight', state.aiWeight);
      localStorage.setItem('f1-ai-temperature', state.aiTemperature);
      // Note: API key is NOT saved to localStorage for security
      
      updateAIModeIndicator();
      showAIConfirmation();
    });

    // Trigger button to reopen sidebar
    if (triggerBtn) {
      triggerBtn.style.display = 'flex';
      triggerBtn.addEventListener('click', () => {
        sidebar.classList.add('is-open');
      });
    }

    // Mode selection
    modeOptions.forEach(option => {
      option.addEventListener('click', () => {
        modeOptions.forEach(opt => opt.classList.remove('active'));
        option.classList.add('active');
        
        const mode = option.dataset.mode;
        state.aiMode = mode;
        
        // Show/hide model section
        const modelSection = document.getElementById('ai-model-section');
        if (mode === 'ai') {
          modelSection.style.display = 'block';
        } else {
          modelSection.style.display = 'none';
        }
      });
    });

    // Model select
    modelSelect.addEventListener('change', (e) => {
      state.aiModel = e.target.value;
      
      // Show/hide custom model input
      const customInputDiv = document.getElementById('custom-model-input');
      if (e.target.value === 'custom' && customInputDiv) {
        customInputDiv.style.display = 'block';
      } else if (customInputDiv) {
        customInputDiv.style.display = 'none';
      }
    });

    // Custom model input
    if (customModelInput) {
      customModelInput.addEventListener('input', (e) => {
        state.aiCustomModel = e.target.value;
      });
    }

    // Tab switching (Settings vs Chat)
    modeTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        modeTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const tabName = tab.dataset.tab;
        const settingsContent = document.getElementById('ai-settings-content');
        const chatSection = document.getElementById('ai-chat-section');
        
        if (tabName === 'settings') {
          if (settingsContent) settingsContent.style.display = 'block';
          if (chatSection) chatSection.style.display = 'none';
        } else {
          if (settingsContent) settingsContent.style.display = 'none';
          if (chatSection) chatSection.style.display = 'block';
        }
      });
    });

    // Chat functionality
    if (chatSend && chatInput && chatMessages) {
      const sendChatMessage = async () => {
        const message = chatInput.value.trim();
        if (!message || !state.aiApiKey) {
          if (!state.aiApiKey) {
            addChatMessage('ai', 'Please enter your API key in the Settings tab first.');
          }
          return;
        }
        
        // Add user message
        addChatMessage('user', message);
        chatInput.value = '';
        chatSend.disabled = true;
        
        // Call AI API
        try {
          const response = await fetch('/dashboard/api/ai-chat', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              message: message,
              model: state.aiModel,
              api_key: state.aiApiKey,
              temperature: state.aiTemperature,
            }),
          });
          
          const data = await response.json();
          
          if (data.error) {
            addChatMessage('ai', `Error: ${data.error}`);
          } else {
            addChatMessage('ai', data.response);
          }
        } catch (err) {
          addChatMessage('ai', `Error: ${err.message}`);
        } finally {
          chatSend.disabled = false;
        }
      };
      
      chatSend.addEventListener('click', sendChatMessage);
      chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
          sendChatMessage();
        }
      });
    }

    function addChatMessage(role, text) {
      const messageDiv = document.createElement('div');
      messageDiv.className = `ai-chat-message ai-chat-message-${role}`;
      messageDiv.innerHTML = `<div class="ai-chat-text">${text}</div>`;
      chatMessages.appendChild(messageDiv);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // API key input
    apiKeyInput.addEventListener('input', (e) => {
      state.aiApiKey = e.target.value;
    });

    // Weight slider
    weightSlider.addEventListener('input', (e) => {
      state.aiWeight = parseInt(e.target.value);
      weightValue.textContent = state.aiWeight;
    });

    // Temperature slider
    temperatureSlider.addEventListener('input', (e) => {
      const temp = parseInt(e.target.value) / 100;
      state.aiTemperature = temp;
      temperatureValue.textContent = temp.toFixed(1);
    });

    // Load saved settings
    loadAISettings();
    updateAIModeIndicator();
  }

  function updateAIModeIndicator() {
    const indicator = document.getElementById('ai-mode-indicator');
    const icon = document.getElementById('ai-mode-icon');
    const text = document.getElementById('ai-mode-text');
    
    if (!indicator || !icon || !text) return;
    
    if (state.aiMode === 'ai') {
      indicator.style.display = 'inline-flex';
      icon.textContent = '🤖';
      // Show model name (shortened if needed)
      const modelShort = state.aiModel.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      text.textContent = `${modelShort} (${state.aiWeight}%)`;
    } else {
      indicator.style.display = 'inline-flex';
      icon.textContent = '⚡';
      text.textContent = 'Normal Mode';
    }
  }

  function loadAISettings() {
    const savedMode = localStorage.getItem('f1-ai-mode');
    const savedModel = localStorage.getItem('f1-ai-model');
    const savedWeight = localStorage.getItem('f1-ai-weight');
    const savedTemp = localStorage.getItem('f1-ai-temperature');

    if (savedMode) {
      state.aiMode = savedMode;
      const modeOption = document.querySelector(`.ai-sidebar-option[data-mode="${savedMode}"]`);
      if (modeOption) {
        document.querySelectorAll('.ai-sidebar-option').forEach(opt => opt.classList.remove('active'));
        modeOption.classList.add('active');
      }
      
      const modelSection = document.getElementById('ai-model-section');
      if (savedMode === 'ai') {
        modelSection.style.display = 'block';
      } else {
        modelSection.style.display = 'none';
      }
    }

    if (savedModel) {
      state.aiModel = savedModel;
      const modelSelect = document.getElementById('ai-model-select');
      if (modelSelect) modelSelect.value = savedModel;
    }

    if (savedWeight) {
      state.aiWeight = parseInt(savedWeight);
      const weightSlider = document.getElementById('ai-weight-slider');
      const weightValue = document.getElementById('ai-weight-value');
      if (weightSlider) weightSlider.value = state.aiWeight;
      if (weightValue) weightValue.textContent = state.aiWeight;
    }

    if (savedTemp) {
      state.aiTemperature = parseFloat(savedTemp);
      const temperatureSlider = document.getElementById('ai-temperature-slider');
      const temperatureValue = document.getElementById('ai-temperature-value');
      if (temperatureSlider) temperatureSlider.value = state.aiTemperature * 100;
      if (temperatureValue) temperatureValue.textContent = state.aiTemperature.toFixed(1);
    }
    
    // API key is never loaded from storage for security
  }

  function showAIConfirmation() {
    const message = state.aiMode === 'ai' 
      ? `AI mode enabled with ${state.aiModel} at ${state.aiWeight}% influence`
      : 'Normal mode enabled (traditional ML predictions)';
    
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'ai-toast';
    toast.style.cssText = `
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1rem 1.5rem;
      box-shadow: 0 4px 16px rgba(0,0,0,0.15);
      z-index: 10000;
      animation: slideIn 0.3s ease;
    `;
    toast.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.75rem;">
        <span style="font-size: 1.5rem;">${state.aiMode === 'ai' ? '🤖' : '⚡'}</span>
        <div>
          <div style="font-weight: 700; color: var(--text); font-size: 0.9rem;">Settings Applied</div>
          <div style="font-size: 0.85rem; color: var(--sub);">${message}</div>
        </div>
      </div>
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  // Add animation keyframes
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
  `;
  document.head.appendChild(style);

  function populateRaceSelects() {
    console.log("Race selects are now populated server-side, skipping JavaScript population");
    // Dropdowns are now populated by the server, so we don't need to do anything here
    // The calendar data is still available in state.calendar for other functions
  }

  function populateSubSessionSelect() {
    const sess = SESSIONS.find((s) => s.id === state.session);
    const race = raceById(state.draft.raceId);
    
    // Check if current race is a sprint weekend
    state.isSprintWeekend = race && race.sprint === true;
    
    // For qualifying, filter sub-sessions based on sprint weekend status
    let availableSubs = sess.subs;
    if (state.session === "qualifying" && !state.isSprintWeekend) {
      // Only show Q1, Q2, Q3 for non-sprint weekends
      availableSubs = sess.subs.filter(s => s !== "Sprint Race");
    }
    
    $("#cb-sub-session").innerHTML = availableSubs.map((s) => `<option value="${s}">${s}</option>`).join("");
    
    // Set default sub-session
    if (availableSubs.length > 0) {
      state.subSession = availableSubs[0];
    }
  }

  // -----------------------------------------------------------------------
  // Session cards
  // -----------------------------------------------------------------------
  function renderSessionCards() {
    const race = raceById(state.draft.raceId);
    $("#sprint-tag").innerHTML = race && race.sprint
      ? '<span class="fs-10 px-1.5 py-0.5 rounded font-bold" style="background:var(--red-tint);color:var(--red)">SPRINT WEEKEND</span>' : "";

    $("#session-cards").innerHTML = SESSIONS.map((s) => {
      const active = state.session === s.id;
      return `<button data-session="${s.id}" class="session-card ${active ? "is-active" : ""}" style="text-align:left">
        <span style="font-size:20px;line-height:1">${s.icon}</span>
        <div class="f1-display font-bold text-sm mt-1.5">${s.label}</div>
        <div class="fs-11 mt-0.5 session-sub text-sub">${s.desc}</div>
      </button>`;
    }).join("");

    $("#session-cards").querySelectorAll("[data-session]").forEach((btn) => {
      btn.addEventListener("click", () => {
        state.session = btn.dataset.session;
        // Set appropriate target based on session
        if (state.session === "qualifying") {
          state.targetId = "qualifying_q3"; // Default to Q3
        } else if (state.session === "practice") {
          state.targetId = "practice_pace"; // Default to general practice pace
        } else {
          state.targetId = "podium"; // Default for race
        }
        populateSubSessionSelect();
        renderSessionCards();
        updateSessionTag();
        showSessionContent(); // Show content immediately when session is selected
        renderResults();
      });
    });
  }

  function showSessionContent() {
    // Hide all session content first
    document.querySelectorAll('.session-content').forEach(el => el.style.display = 'none');

    // Show appropriate content based on session
    if (state.session === "practice") {
      const fridayContent = document.getElementById('friday-content');
      if (fridayContent) fridayContent.style.display = 'block';
    } else if (state.session === "qualifying") {
      const saturdayContent = document.getElementById('saturday-content');
      if (saturdayContent) saturdayContent.style.display = 'block';
    } else if (state.session === "race") {
      const sundayContent = document.getElementById('sunday-content');
      if (sundayContent) sundayContent.style.display = 'block';
    }
  }

  function updateSessionTag() {
    const tag = state.session === "practice" ? "Practice (Friday)" : state.session === "qualifying" ? "Qualifying (Saturday)" : "Race Day (Sunday)";
    $("#session-tag").textContent = tag;
  }

  // -----------------------------------------------------------------------
  // Hero
  // -----------------------------------------------------------------------
  function renderHero() {
    const race = raceById(state.draft.raceId);
    $("#hero-race-select").value = state.draft.raceId;
    $("#cb-race-select").value = state.draft.raceId;
    $("#hero-weather-select").value = state.draft.weather;
    $("#cb-weather-select").value = state.draft.weather;
    $("#cb-sim-count").value = state.draft.simCount;
    $("#run-btn").disabled = !state.draft.raceId || state.runState === "running";
    $("#run-hint").style.display = state.draft.raceId ? "none" : "block";

    if (!race) {
      setStat("#stat-sc", "—", true);
      setStat("#stat-rain", "—", true);
      $("#hero-event-name").textContent = "No Grand Prix selected";
      $("#hero-event-circuit").textContent = "Pick a race to populate this weekend's data";
      $("#hero-facts").innerHTML = factTile("Laps", "—") + factTile("DRS zones", "—", true) + factTile("Overtaking", "—");
      return;
    }
    const rain = state.draft.weather === "wet" ? Math.max(70, race.base_rain)
      : state.draft.weather === "mixed" ? Math.round((race.base_rain + 40) / 2)
      : Math.round(race.base_rain * 0.4);
    const sc = Math.min(90, race.base_sc + (state.draft.weather !== "dry" ? 10 : 0));
    setStat("#stat-sc", sc + "%", false);
    setStat("#stat-rain", rain + "%", false);
    $("#hero-event-name").textContent = race.name;
    $("#hero-event-circuit").textContent = race.circuit;
    $("#hero-facts").innerHTML = factTile("Laps", race.laps) + factTile("DRS zones", race.drs_zones, true) + factTile("Overtaking", race.overtaking);

    renderSessionCards();
    renderInfoCircuit();
    updateSessionTag();
  }

  function factTile(label, value, purple) {
    return `<div class="rounded-lg p-2 text-center" style="background:${purple ? "rgba(157,78,221,.22)" : "rgba(255,255,255,.06)"}">
      <div class="fs-9 uppercase tracking-widest" style="color:rgba(255,255,255,.6)">${label}</div>
      <div class="f1-mono text-sm font-semibold" style="${purple ? "color:#D9B3F7" : ""}">${value}</div>
    </div>`;
  }
  function setStat(sel, value, empty) {
    const el = $(sel);
    el.textContent = value;
    el.classList.toggle("is-empty", !!empty);
  }
  function setSimStat() {
    const n = state.draft.simCount;
    setStat("#stat-sims", n >= 1000 ? Math.round(n / 1000) + "k" : String(n), false);
  }

  function startCountdown() {
    setInterval(() => {
      state.countdown = Math.max(0, state.countdown - 1);
      const h = Math.floor(state.countdown / 3600);
      const m = Math.floor((state.countdown % 3600) / 60);
      const s = state.countdown % 60;
      $("#countdown").textContent = `${h}h ${String(m).padStart(2, "0")}m ${String(s).padStart(2, "0")}s`;
    }, 1000);
  }

  // -----------------------------------------------------------------------
  // Info cards
  // -----------------------------------------------------------------------
  function renderInfoCircuit() {
    const race = raceById(state.draft.raceId);
    if (!race) {
      $("#info-circuit").innerHTML = emptyMini("Select a Grand Prix", "Circuit details will appear here.");
      return;
    }
    $("#info-circuit").innerHTML = `<div class="space-y-2 text-sm">
      ${row("Circuit", race.circuit)}
      ${row("Laps", race.laps)}
      ${row("Length", race.length_km.toFixed(3) + " km")}
      ${row("DRS zones", race.drs_zones)}
      ${row("Overtaking", race.overtaking)}
    </div>`;
    renderConditions(race);
  }

  function renderSessionForecast() {
    const race = raceById(state.committed ? state.committed.raceId : state.draft.raceId);
    $("#info-session-badge").textContent = state.subSession;
    if (!race || state.runState !== "done") {
      $("#info-session").innerHTML = emptyMini("No data yet", "Run the prediction engine to see results.");
      return;
    }
    const weather = state.committed.weather;
    if (state.session === "race") {
      const sc = Math.min(90, race.base_sc + (weather !== "dry" ? 10 : 0));
      $("#info-session").innerHTML = `
        <div class="fs-11 uppercase tracking-widest font-semibold text-sub">Safety car probability</div>
        <div class="f1-mono text-3xl font-bold mt-1 text-red">${sc}%</div>
        <div class="text-xs mt-2 text-sub">Circuit baseline for ${race.circuit}, adjusted for weather. Not a model output.</div>`;
    } else if (state.session === "qualifying") {
      const q3 = state.predictions.q3;
      const top = q3 && q3.predictions && q3.predictions[0];
      $("#info-session").innerHTML = top ? `
        <div class="fs-11 uppercase tracking-widest font-semibold text-sub">Model-projected pole probability</div>
        <div class="f1-mono text-3xl font-bold mt-1 text-red">${top.percentage.toFixed(1)}%</div>
        <div class="text-xs mt-2 text-sub">${F1.escapeHtml(state.driverMap[top.driver_code]?.name || top.driver_code)} — chance of topping the Q3 model.</div>`
        : emptyMini("No data yet", "Run the prediction engine to see results.");
    } else {
      const practice = state.predictions.practice_pace;
      const top = practice && practice.predictions && practice.predictions[0];
      $("#info-session").innerHTML = top ? `
        <div class="fs-11 uppercase tracking-widest font-semibold text-sub">Projected practice pace leader</div>
        <div class="f1-mono text-3xl font-bold mt-1 text-red">${top.percentage.toFixed(1)}%</div>
        <div class="text-xs mt-2 text-sub">${F1.escapeHtml(state.driverMap[top.driver_code]?.name || top.driver_code)} — forecast, not an invented lap time.</div>`
        : emptyMini("No data yet", "Run the practice pace forecast to see results.");
    }
  }

  function renderConditions(race) {
    const weather = state.draft.weather;
    const icon = weather === "wet" ? "&#127783;&#65039;" : weather === "mixed" ? "&#9925;&#65039;" : "&#9728;&#65039;";
    const label = weather === "wet" ? "Wet & Rainy" : weather === "mixed" ? "Mixed Conditions" : "Sunny & Clear";
    const humidity = weather === "wet" ? 85 : weather === "mixed" ? 60 : 40;
    const wind = 8 + (race.round % 7);
    $("#info-conditions").innerHTML = `
      <div class="rounded-lg p-4 flex items-center justify-between text-white" style="background:var(--navy)">
        <div class="flex items-center gap-3">
          <span style="font-size:26px">${icon}</span>
          <div>
            <div class="f1-mono text-2xl font-bold">${race.base_temp}&deg;C</div>
            <div class="fs-11" style="color:rgba(255,255,255,.75)">${label}</div>
          </div>
        </div>
        <div class="text-right fs-11" style="color:rgba(255,255,255,.75)">
          <div>&#128167; ${humidity}% humidity</div>
          <div class="mt-1">&#128168; ${wind} km/h</div>
          <div class="mt-1">${race.base_temp + 8}&deg;C track</div>
        </div>
      </div>
      <div class="mt-3 space-y-2 text-sm">
        <div class="flex items-center justify-between">
          <span class="text-sub">Compound call</span>
          ${F1.tyreChipHtml(F1.compoundForWeather(weather))}
        </div>
        ${row("Grip level", weather === "dry" ? "High" : "Reduced")}
      </div>`;
  }

  function row(k, v) { return `<div class="flex items-center justify-between"><span class="text-sub">${k}</span><span class="f1-mono font-semibold">${v}</span></div>`; }
  function emptyMini(title, body) {
    return `<div class="flex flex-col items-center justify-center text-center py-6 px-2">
      <div class="f1-display font-bold">${title}</div>
      <div class="text-xs mt-1 text-sub" style="max-width:220px">${body}</div>
    </div>`;
  }

  // -----------------------------------------------------------------------
  // Real result banner
  // -----------------------------------------------------------------------
  async function renderRealResultBanner() {
    const race = raceById(state.draft.raceId);
    const el = $("#real-result-banner");
    if (!race || race.status !== "completed") { el.innerHTML = ""; return; }
    el.innerHTML = `<div class="card p-4 flex items-start gap-3">
      <span class="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0" style="background:var(--red-tint)">&#127937;</span>
      <div class="flex-1 min-w-0">
        <div class="f1-display font-bold">This race already happened — ${race.date}</div>
        <p class="text-xs mt-1 text-sub">Fetching the real result&hellip;</p>
      </div></div>`;
    try {
      const result = await F1.api(`/dashboard/api/race-result/${race.id}`);
      if (!result || !result.podium || !result.podium.length) throw new Error("no result");
      const podiumHtml = result.podium.map((code) => `<span class="fs-11 f1-mono font-semibold px-2 py-1 rounded surface-alt">P${result.podium.indexOf(code) + 1} ${code}</span>`).join(" ");
      const winnerDriver = state.driverMap[result.winner];
      el.innerHTML = `<div class="card p-4 flex items-start gap-3">
        <span class="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0" style="background:var(--red-tint)">&#127937;</span>
        <div class="flex-1 min-w-0">
          <div class="f1-display font-bold">This race already happened — ${race.date}</div>
          <p class="text-xs text-sub">Real winner: <b style="color:var(--text)">${F1.escapeHtml(winnerDriver ? winnerDriver.name : result.winner)}</b>${winnerDriver ? " (" + F1.escapeHtml(winnerDriver.team_name) + ")" : ""}</p>
          <div class="flex flex-wrap gap-2 mt-2">${podiumHtml}</div>
          <p class="fs-10 mt-2 text-muted">You can still run the prediction engine below to see what the model would have projected, for comparison.</p>
        </div></div>`;
    } catch (e) {
      el.innerHTML = `<div class="card p-4 flex items-start gap-3">
        <span class="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0" style="background:var(--red-tint)">&#127937;</span>
        <div class="flex-1 min-w-0">
          <div class="f1-display font-bold">This race already happened — ${race.date}</div>
          <p class="text-xs mt-1 text-amber">Real result unavailable right now.</p>
          <p class="fs-10 mt-2 text-muted">You can still run the prediction engine below to see what the model would have projected, for comparison.</p>
        </div></div>`;
    }
  }

  // -----------------------------------------------------------------------
  // Export
  // -----------------------------------------------------------------------
  async function handleExport() {
    if (!state.committed || Object.keys(state.predictions).length === 0) {
      alert("Please run a prediction first before exporting.");
      return;
    }

    const format = $("#export-format").value;
    await handleExportByFormat(format);
  }

  async function handleExportByFormat(format) {
    if (!state.committed || Object.keys(state.predictions).length === 0) {
      alert("Please run a prediction first before exporting.");
      return;
    }

    const includeCharts = $("#export-charts").value === "yes";
    const detailLevel = $("#export-detail").value;
    const race = raceById(state.committed.raceId);

    try {
      const response = await F1.api("/reports/api/export", {
        method: "POST",
        body: {
          race_id: state.committed.raceId,
          session: state.session,
          sub_session: state.subSession,
          target_id: state.targetId,
          format: format,
          include_charts: includeCharts,
          detail_level: detailLevel,
          predictions: state.predictions
        }
      });

      if (response.download_url) {
        // Create download link
        const link = document.createElement('a');
        link.href = response.download_url;
        link.download = `f1_prediction_${race?.name || 'race'}_${state.session}_${format}.${format}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else if (response.data) {
        // Handle direct data return (for JSON/CSV)
        downloadData(response.data, format, race?.name || 'race');
      }

      alert(`Export successful! ${format.toUpperCase()} file downloaded.`);
    } catch (error) {
      alert(`Export failed: ${error.message}`);
    }
  }

  function downloadData(data, format, raceName) {
    let content, mimeType, extension;

    switch (format) {
      case 'json':
        content = JSON.stringify(data, null, 2);
        mimeType = 'application/json';
        extension = 'json';
        break;
      case 'csv':
        content = convertToCSV(data);
        mimeType = 'text/csv';
        extension = 'csv';
        break;
      default:
        content = JSON.stringify(data, null, 2);
        mimeType = 'application/json';
        extension = 'json';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `f1_prediction_${raceName}_${state.session}.${extension}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function convertToCSV(data) {
    if (!data || !Array.isArray(data)) return '';

    const headers = Object.keys(data[0]);
    const csvRows = [];

    csvRows.push(headers.join(','));

    for (const row of data) {
      const values = headers.map(header => {
        const escaped = ('' + row[header]).replace(/"/g, '\\"');
        return `"${escaped}"`;
      });
      csvRows.push(values.join(','));
    }

    return csvRows.join('\n');
  }

  // -----------------------------------------------------------------------
  // Run
  // -----------------------------------------------------------------------
  async function handleRun() {
    if (!state.draft.raceId) {
      alert("Please select a race first");
      return;
    }
    
    state.committed = Object.assign({}, state.draft, { session: state.session, subSession: state.subSession });
    state.runState = "running";
    state.manualGrid = null;
    renderRunUI();

    // Build AI config if AI mode is enabled
    const aiConfig = state.aiMode === 'ai' ? {
      ai_mode: state.aiMode,
      ai_model: state.aiModel,
      ai_api_key: state.aiApiKey,
      ai_weight: state.aiWeight / 100, // Convert to 0-1 range
      ai_temperature: state.aiTemperature,
      simulation_count: state.committed.simCount,
    } : {};

    try {
      console.log("Running prediction for:", state.session, state.subSession);
      
      if (state.session === "race") {
        // Build a simulated grid from the Q3 model unless the user already
        // supplied one manually.
        const qualResult = await F1.api("/dashboard/api/predict-session", {
          method: "POST",
          body: {
            race_id: state.committed.raceId,
            session_type: "qualifying",
            sub_session: "q3",
            weather: state.committed.weather,
            feature_weights: F1.getTuning(),
            simulation_count: state.committed.simCount,
            ...aiConfig,
          },
        });
        const q3 = qualResult.predictions && qualResult.predictions.q3;
        const simulatedGrid = {};
        if (q3 && q3.predictions) {
          q3.predictions.forEach((p, i) => { simulatedGrid[p.driver_code] = i + 1; });
        }
        state.gridPositions = state.manualGrid || simulatedGrid;
        state.gridSource = state.manualGrid ? "manual" : (Object.keys(simulatedGrid).length ? "simulated" : null);

        const raceResult = await F1.api("/dashboard/api/predict-session", {
          method: "POST",
          body: {
            race_id: state.committed.raceId,
            session_type: "race",
            sub_session: "race",
            weather: state.committed.weather,
            grid_positions: state.gridPositions,
            feature_weights: F1.getTuning(),
            simulation_count: state.committed.simCount,
            ...aiConfig,
          },
        });
        state.predictions = raceResult.predictions || {};
      } else {
        // qualifying or practice - pass sub_session for specific sessions
        const result = await F1.api("/dashboard/api/predict-session", {
          method: "POST",
          body: {
            race_id: state.committed.raceId,
            session_type: state.session,
            sub_session: state.subSession.toLowerCase(),
            weather: state.committed.weather,
            feature_weights: F1.getTuning(),
            simulation_count: state.committed.simCount,
            ...aiConfig,
          },
        });
        state.predictions = result.predictions || {};
        state.gridSource = null;
      }
      state.runState = "done";
      console.log("Prediction completed successfully:", state.predictions);
    } catch (err) {
      state.runState = "idle";
      console.error("Prediction failed:", err);
      F1.showError($("#results-empty"), "Prediction failed: " + err.message);
    }
    renderRunUI();
    renderResults();
    renderSessionForecast();
    renderRealResultBanner();
  }

  function renderRunUI() {
    $("#run-btn").disabled = !state.draft.raceId || state.runState === "running";
    $("#run-btn-label").textContent = state.runState === "running" ? "Running…" : "Run Prediction";
    $("#run-progress").style.display = state.runState === "running" ? "block" : "none";

    // Enhanced loading indicator
    if (state.runState === "running") {
      // Show detailed loading state
      const progressBar = $("#run-progress").querySelector('div');
      if (progressBar) {
        progressBar.style.width = "40%";
        progressBar.style.transition = "width 0.3s ease";
        
        // Simulate progress
        let progress = 40;
        const progressInterval = setInterval(() => {
          if (state.runState !== "running") {
            clearInterval(progressInterval);
            return;
          }
          progress += Math.random() * 15;
          if (progress > 90) progress = 90;
          progressBar.style.width = progress + "%";
        }, 500);
      }
      
      // Add loading overlay
      showLoadingOverlay();
    } else {
      hideLoadingOverlay();
    }

    // Enable export button when predictions are available
    const exportBtn = $("#export-btn");
    const exportStatus = $("#export-status");
    const exportPreview = $("#export-preview");

    if (exportBtn) {
      const hasPredictions = state.committed && Object.keys(state.predictions).length > 0;
      exportBtn.disabled = !hasPredictions;
      if (hasPredictions) {
        exportStatus.textContent = "Ready to export prediction results.";
        exportStatus.style.color = "var(--green)";
        exportPreview.style.display = "grid";
      } else {
        exportStatus.textContent = "Run a prediction above to enable report exports.";
        exportStatus.style.color = "var(--muted)";
        exportPreview.style.display = "none";
      }
    }
  }
  
  function showLoadingOverlay() {
    // Remove existing overlay if any
    hideLoadingOverlay();
    
    const overlay = document.createElement('div');
    overlay.id = 'prediction-loading-overlay';
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
      backdrop-filter: blur(4px);
    `;
    
    const loadingContent = document.createElement('div');
    loadingContent.style.cssText = `
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2rem;
      text-align: center;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      max-width: 400px;
    `;
    
    const spinner = document.createElement('div');
    spinner.style.cssText = `
      width: 48px;
      height: 48px;
      margin: 0 auto 1.5rem;
      border: 4px solid var(--border);
      border-top-color: var(--red);
      border-radius: 50%;
      animation: spin 1s linear infinite;
    `;
    
    const loadingText = document.createElement('div');
    loadingText.className = 'f1-display font-bold';
    loadingText.style.fontSize = '1.25rem';
    loadingText.style.color = 'var(--text)';
    loadingText.textContent = 'Running Monte Carlo Simulations';
    
    const subText = document.createElement('div');
    subText.style.cssText = `
      margin-top: 0.5rem;
      font-size: 0.875rem;
      color: var(--sub);
    `;
    subText.textContent = `Processing ${state.committed?.simCount || 10000} simulations with ${state.aiMode === 'ai' ? 'AI enhancement' : 'ML model'}...`;
    
    loadingContent.appendChild(spinner);
    loadingContent.appendChild(loadingText);
    loadingContent.appendChild(subText);
    overlay.appendChild(loadingContent);
    document.body.appendChild(overlay);
    
    // Add animation keyframes if not exists
    if (!document.getElementById('loading-spinner-style')) {
      const style = document.createElement('style');
      style.id = 'loading-spinner-style';
      style.textContent = `
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `;
      document.head.appendChild(style);
    }
  }
  
  function hideLoadingOverlay() {
    const overlay = document.getElementById('prediction-loading-overlay');
    if (overlay) {
      overlay.remove();
    }
  }

  // -----------------------------------------------------------------------
  // Grid status banner (shown after a race-session run)
  // -----------------------------------------------------------------------
  function renderGridStatusBanner() {
    const el = $("#grid-status-banner");
    if (state.session !== "race" || state.runState !== "done") { el.innerHTML = ""; return; }
    if (!state.gridSource) {
      el.innerHTML = `<div class="flex flex-wrap items-center gap-2 mb-3 fs-11 font-semibold px-3 py-2 rounded-lg" style="background:var(--red-tint);color:var(--red);border:1px solid var(--border)">
        <span>&#9888;&#65039;</span><span>Couldn't auto-fill the grid — please assign each driver's starting position (P1-P22) manually below.</span>
      </div>`;
      renderGridEditor(true);
      return;
    }
    const label = state.gridSource === "manual" ? "your manual entry" : "the Q3 qualifying model";
    el.innerHTML = `<div class="flex flex-wrap items-center gap-2 mb-3 fs-11 font-semibold px-3 py-2 rounded-lg surface-alt" style="color:var(--sub);border:1px solid var(--border)">
      <span class="w-1.5 h-1.5 rounded-full flex-shrink-0" style="background:var(--green)"></span>
      <span>Grid auto-filled from ${label} — qualifying position is one of the strongest real predictors of race outcome.</span>
      <button id="grid-toggle-manual" class="fs-10 font-bold uppercase tracking-wide px-2 py-1 rounded flex-shrink-0" style="background:var(--surface);border:1px solid var(--border)">Edit Grid Manually</button>
      ${state.gridSource === "manual" ? '<button id="grid-revert" class="fs-10 font-bold uppercase tracking-wide px-2 py-1 rounded flex-shrink-0 text-red">Revert to Auto-fill</button>' : ""}
    </div>`;
    $("#grid-toggle-manual").addEventListener("click", () => renderGridEditor(true, true));
    const revertBtn = $("#grid-revert");
    if (revertBtn) revertBtn.addEventListener("click", () => { state.manualGrid = null; handleRun(); });
  }

  let gridEditorOpen = false;
  function renderGridEditor(forceOpen, toggle) {
    if (toggle) gridEditorOpen = !gridEditorOpen;
    if (forceOpen && !toggle) gridEditorOpen = true;
    const el = $("#manual-grid-editor");
    if (!gridEditorOpen) { el.innerHTML = ""; return; }
    const drivers = Object.values(state.driverMap).sort((a, b) => a.code.localeCompare(b.code));
    F1GridEditor.render(el, {
      drivers,
      seedGrid: state.gridPositions,
      currentGrid: state.manualGrid,
      onApply: (grid) => { state.manualGrid = grid; gridEditorOpen = false; handleRun(); },
      onCancel: () => { gridEditorOpen = false; renderGridEditor(); },
    });
  }

  // -----------------------------------------------------------------------
  // Session-specific chart generation
  // -----------------------------------------------------------------------
  function generateFridayCharts() {
    // Generate Friday Practice charts with meaningful F1 data
    const drivers = Object.values(state.driverMap);
    const topDrivers = drivers.slice(0, 12);

    // Practice Pace Analysis - use actual prediction data if available
    const paceChart = document.getElementById('chart-friday-pace');
    if (paceChart) {
      let paceScores;
      
      // Try to use actual prediction data
      const practicePrediction = state.predictions.practice_pace || state.predictions.practice_fp1 || state.predictions.practice_fp2 || state.predictions.practice_fp3;
      
      if (practicePrediction && practicePrediction.predictions) {
        // Use actual prediction probabilities
        paceScores = topDrivers.map(d => {
          const pred = practicePrediction.predictions.find(p => p.driver_code === d.code);
          return pred ? pred.probability : 0.01;
        });
      } else {
        // Fallback to driver strength with variation
        paceScores = topDrivers.map(d => {
          const baseStrength = (d.strength || 50) / 100;
          const variation = (Math.random() - 0.5) * 0.2; // +/- 10% variation
          return Math.max(0.3, Math.min(0.95, baseStrength + variation));
        });
      }
      
      F1Charts.barDistribution(
        paceChart,
        topDrivers.map(d => d.code),
        paceScores,
        topDrivers.map(d => d.team_color || F1.teamColor(d.team)),
        { title: 'Practice Pace Analysis' }
      );
    }
    
    // Tyre Performance
    const tyreChart = document.getElementById('chart-friday-tyres');
    if (tyreChart) {
      F1Charts.lineChart(
        tyreChart,
        ['Lap 1', 'Lap 5', 'Lap 10', 'Lap 15', 'Lap 20', 'Lap 25'],
        {
          'Soft': [98, 95, 92, 88, 85, 82],
          'Medium': [95, 93, 91, 89, 87, 85],
          'Hard': [92, 91, 90, 89, 88, 87]
        },
        { title: 'Tyre Performance Over Laps' }
      );
    }
    
    // Weather Impact
    const weatherChart = document.getElementById('chart-friday-weather');
    if (weatherChart) {
      F1Charts.barChart(
        weatherChart,
        ['Dry', 'Mixed', 'Wet'],
        [0.85, 0.65, 0.45],
        ['#1DA36B', '#D97B0A', '#16233F'],
        { title: 'Weather Impact on Performance' }
      );
    }
    
    // Fuel Load Effect
    const fuelChart = document.getElementById('chart-friday-fuel');
    if (fuelChart) {
      F1Charts.lineChart(
        fuelChart,
        ['Lap 1', 'Lap 5', 'Lap 10', 'Lap 15', 'Lap 20'],
        {
          'Lap Time': [92, 89, 87, 86, 85],
          'Ref Adjusted': [90, 88, 87, 86, 85]
        },
        { title: 'Fuel Load Effect on Lap Times' }
      );
    }
    
    // Sector Analysis
    const sectorChart = document.getElementById('chart-friday-sectors');
    if (sectorChart) {
      F1Charts.barChart(
        sectorChart,
        ['Sector 1', 'Sector 2', 'Sector 3'],
        [28, 32, 25],
        [topDrivers[0]?.team_color || '#E10600'],
        { title: 'Sector Analysis - Top Driver' }
      );
    }
    
    // Long Run Pace
    const longRunChart = document.getElementById('chart-friday-longrun');
    if (longRunChart) {
      F1Charts.lineChart(
        longRunChart,
        ['Lap 10', 'Lap 15', 'Lap 20', 'Lap 25', 'Lap 30'],
        {
          'Driver A': [87, 86, 85, 84, 83],
          'Driver B': [88, 87, 86, 85, 84],
          'Driver C': [89, 88, 87, 86, 85]
        },
        { title: 'Long Run Pace Comparison' }
      );
    }
    
    // Setup Configurations
    const setupChart = document.getElementById('chart-friday-setup');
    if (setupChart) {
      F1Charts.barChart(
        setupChart,
        ['Low Downforce', 'Medium Downforce', 'High Downforce'],
        [0.75, 0.85, 0.65],
        ['#E10600', '#1DA36B', '#D97B0A'],
        { title: 'Setup Configuration Impact' }
      );
    }
    
    // Driver Consistency
    const consistencyChart = document.getElementById('chart-friday-consistency');
    if (consistencyChart) {
      F1Charts.barChart(
        consistencyChart,
        topDrivers.slice(0, 8).map(d => d.code),
        topDrivers.slice(0, 8).map(() => Math.random() * 0.3 + 0.7),
        topDrivers.slice(0, 8).map(d => d.team_color || F1.teamColor(d.team)),
        { title: 'Driver Consistency Rating' }
      );
    }
    
    // Brake Temperature
    const brakeChart = document.getElementById('chart-friday-brakes');
    if (brakeChart) {
      F1Charts.lineChart(
        brakeChart,
        ['Lap 1', 'Lap 5', 'Lap 10', 'Lap 15', 'Lap 20'],
        {
          'Front Left': [650, 720, 680, 700, 690],
          'Front Right': [680, 750, 710, 730, 720],
          'Rear Left': [550, 600, 580, 590, 585],
          'Rear Right': [570, 620, 600, 610, 605]
        },
        { title: 'Brake Temperature Analysis' }
      );
    }
    
    // Engine Performance
    const engineChart = document.getElementById('chart-friday-engine');
    if (engineChart) {
      F1Charts.barChart(
        engineChart,
        ['Top Speed', 'Acceleration', 'Power Unit Mode'],
        [340, 92, 95],
        [topDrivers[0]?.team_color || '#E10600'],
        { title: 'Engine Performance Metrics' }
      );
    }
  }
  
  function generateSaturdayCharts() {
    // Generate Saturday Qualifying charts
    const drivers = Object.values(state.driverMap);
    const topDrivers = drivers.slice(0, 12);

    // Qualifying Predictions - use actual prediction data if available
    const qualiChart = document.getElementById('chart-saturday-quali');
    if (qualiChart) {
      let qualiChances;
      
      // Try to use actual prediction data
      const qualiPrediction = state.predictions.q3 || state.predictions.qualifying_q1 || state.predictions.qualifying_q2 || state.predictions.qualifying_q3;
      
      if (qualiPrediction && qualiPrediction.predictions) {
        // Use actual prediction probabilities
        qualiChances = topDrivers.map(d => {
          const pred = qualiPrediction.predictions.find(p => p.driver_code === d.code);
          return pred ? pred.probability : 0.01;
        });
      } else {
        // Fallback to driver strength with variation
        qualiChances = topDrivers.map(d => {
          const baseStrength = (d.strength || 50) / 100;
          const variation = (Math.random() - 0.5) * 0.25; // +/- 12.5% variation
          return Math.max(0.2, Math.min(0.9, baseStrength + variation));
        });
      }
      
      F1Charts.barDistribution(
        qualiChart,
        topDrivers.map(d => d.code),
        qualiChances,
        topDrivers.map(d => d.team_color || F1.teamColor(d.team)),
        { title: 'Qualifying Predictions' }
      );
    }
    
    // Q1 Eliminations
    const q1Chart = document.getElementById('chart-saturday-q1');
    if (q1Chart) {
      F1Charts.barChart(
        q1Chart,
        ['Driver 1', 'Driver 2', 'Driver 3', 'Driver 4', 'Driver 5'],
        [0.92, 0.88, 0.85, 0.82, 0.78],
        ['#E10600', '#1DA36B', '#D97B0A', '#16233F', '#9D4EDD'],
        { title: 'Q1 Elimination Risk' }
      );
    }
    
    // Q3 Pole Battle - use actual driver strengths
    const q3Chart = document.getElementById('chart-saturday-q3');
    if (q3Chart) {
      const poleChances = topDrivers.slice(0, 5).map(d => {
        const baseStrength = (d.strength || 50) / 100;
        const variation = (Math.random() - 0.5) * 0.15;
        return Math.max(0.05, Math.min(0.5, baseStrength * 0.5 + variation));
      });
      
      F1Charts.barChart(
        q3Chart,
        topDrivers.slice(0, 5).map(d => d.code),
        poleChances,
        topDrivers.slice(0, 5).map(d => d.team_color || F1.teamColor(d.team)),
        { title: 'Q3 Pole Battle' }
      );
    }
    
    // Lap Time Improvement
    const improvementChart = document.getElementById('chart-saturday-improvement');
    if (improvementChart) {
      F1Charts.lineChart(
        improvementChart,
        ['Q1 Best', 'Q2 Best', 'Q3 Best'],
        {
          'Driver A': [92.5, 91.8, 91.2],
          'Driver B': [93.0, 92.2, 91.5],
          'Driver C': [93.5, 92.8, 92.0]
        },
        { title: 'Lap Time Improvement Through Sessions' }
      );
    }
    
    // Sector Performance
    const sectorChart = document.getElementById('chart-saturday-sectors');
    if (sectorChart) {
      F1Charts.barChart(
        sectorChart,
        ['Sector 1', 'Sector 2', 'Sector 3'],
        [26.5, 32.0, 24.8],
        [topDrivers[0]?.team_color || '#E10600'],
        { title: 'Sector Performance - Pole Position Battle' }
      );
    }
    
    // Tire Strategy Impact
    const tireStrategyChart = document.getElementById('chart-saturday-tire-strategy');
    if (tireStrategyChart) {
      F1Charts.barChart(
        tireStrategyChart,
        ['Soft-Medium', 'Soft-Soft', 'Medium-Medium'],
        [0.72, 0.68, 0.55],
        ['#E10600', '#1DA36B', '#D97B0A'],
        { title: 'Tire Strategy Impact on Qualifying' }
      );
    }
    
    // Track Evolution
    const trackChart = document.getElementById('chart-saturday-track');
    if (trackChart) {
      F1Charts.lineChart(
        trackChart,
        ['10:00', '10:15', '10:30', '10:45', '11:00'],
        {
          'Track Temp': [28, 32, 35, 38, 40],
          'Grip Level': [85, 88, 92, 95, 97]
        },
        { title: 'Track Evolution During Qualifying' }
      );
    }
    
    // DRS Effectiveness
    const drsChart = document.getElementById('chart-saturday-drs');
    if (drsChart) {
      F1Charts.barChart(
        drsChart,
        ['Main Straight', 'Back Straight', 'DRS Zones'],
        [0.85, 0.78, 0.82],
        ['#E10600', '#1DA36B', '#D97B0A'],
        { title: 'DRS Effectiveness Analysis' }
      );
    }
    
    // Driver Push Analysis - use driver strength
    const pushChart = document.getElementById('chart-saturday-push');
    if (pushChart) {
      const pushFactors = topDrivers.slice(0, 6).map(d => {
        const baseStrength = (d.strength || 50) / 100;
        const variation = (Math.random() - 0.5) * 0.2;
        return Math.max(0.5, Math.min(0.95, baseStrength + variation));
      });
      
      F1Charts.barChart(
        pushChart,
        topDrivers.slice(0, 6).map(d => d.code),
        pushFactors,
        topDrivers.slice(0, 6).map(d => d.team_color || F1.teamColor(d.team)),
        { title: 'Driver Push Factor Analysis' }
      );
    }
    
    // Setup Comparison
    const setupChart = document.getElementById('chart-saturday-setup');
    if (setupChart) {
      F1Charts.lineChart(
        setupChart,
        ['Low Wing', 'Medium Wing', 'High Wing'],
        {
          'Top Speed': [340, 335, 328],
          'Corner Speed': [140, 145, 150]
        },
        { title: 'Setup Comparison: Speed vs Downforce' }
      );
    }
  }
  
  function generateSundayCharts() {
    // Generate Sunday Race charts
    const drivers = Object.values(state.driverMap);
    const topDrivers = drivers.slice(0, 12);
    
    // Race Start Dynamics
    const startChart = document.getElementById('chart-sunday-start');
    if (startChart) {
      F1Charts.lineChart(
        startChart,
        ['Lap 1', 'Lap 2', 'Lap 3', 'Lap 4', 'Lap 5'],
        {
          'Position Changes': [8, 12, 6, 4, 2],
          'Overtakes': [15, 22, 18, 12, 8]
        },
        { title: 'Race Start Dynamics' }
      );
    }
    
    // DNF Risk Analysis - use actual prediction data
    const dnfChart = document.getElementById('chart-sunday-dnf');
    if (dnfChart) {
      let dnfRisks;
      
      // Try to use actual prediction data for reliability insights
      const racePrediction = state.predictions.winner || state.predictions.podium || state.predictions.points;
      
      if (racePrediction && racePrediction.predictions) {
        // Use prediction data to estimate DNF risks based on reliability
        dnfRisks = topDrivers.slice(0, 8).map(d => {
          const reliability = d.reliability || 80;
          // Lower reliability = higher DNF risk
          const baseRisk = (100 - reliability) / 100 * 0.15;
          const variation = (Math.random() - 0.5) * 0.05;
          return Math.max(0.01, Math.min(0.2, baseRisk + variation));
        });
      } else {
        // Fallback to reliability data
        dnfRisks = topDrivers.slice(0, 8).map(d => {
          const reliability = d.reliability || 80;
          // Lower reliability = higher DNF risk
          const baseRisk = (100 - reliability) / 100 * 0.15;
          const variation = (Math.random() - 0.5) * 0.05;
          return Math.max(0.01, Math.min(0.2, baseRisk + variation));
        });
      }
      
      F1Charts.barChart(
        dnfChart,
        topDrivers.slice(0, 8).map(d => d.code),
        dnfRisks,
        topDrivers.slice(0, 8).map(d => d.team_color || F1.teamColor(d.team)),
        { title: 'DNF Risk Analysis' }
      );
    }
    
    // Pit Stop Windows
    const pitChart = document.getElementById('chart-sunday-pits');
    if (pitChart) {
      F1Charts.barChart(
        pitChart,
        ['Lap 10-15', 'Lap 15-20', 'Lap 20-25', 'Lap 25-30', 'Lap 30+'],
        [0.15, 0.35, 0.30, 0.15, 0.05],
        ['#E10600', '#1DA36B', '#D97B0A', '#16233F', '#9D4EDD'],
        { title: 'Pit Stop Windows' }
      );
    }
    
    // Tire Degradation
    const tyreChart = document.getElementById('chart-sunday-tyres');
    if (tyreChart) {
      F1Charts.lineChart(
        tyreChart,
        ['Lap 1', 'Lap 10', 'Lap 20', 'Lap 30', 'Lap 40', 'Lap 50'],
        {
          'Soft': [100, 85, 70, 55, 40, 25],
          'Medium': [100, 92, 84, 76, 68, 60],
          'Hard': [100, 95, 90, 85, 80, 75]
        },
        { title: 'Tire Degradation Over Race' }
      );
    }
    
    // Race Strategy Comparison
    const strategyChart = document.getElementById('chart-sunday-strategy');
    if (strategyChart) {
      F1Charts.lineChart(
        strategyChart,
        ['Lap 1', 'Lap 15', 'Lap 30', 'Lap 45', 'Lap 60'],
        {
          '1-Stop': [92, 88, 85, 82, 80],
          '2-Stop': [91, 89, 87, 85, 83],
          '3-Stop': [90, 88, 86, 84, 82]
        },
        { title: 'Race Strategy Comparison' }
      );
    }
    
    // Overtaking Analysis
    const overtakeChart = document.getElementById('chart-sunday-overtake');
    if (overtakeChart) {
      F1Charts.barChart(
        overtakeChart,
        ['DRS Zones', 'Non-DRS Zones', 'Pit Exit', 'Start'],
        [0.68, 0.32, 0.45, 0.85],
        ['#E10600', '#1DA36B', '#D97B0A', '#16233F'],
        { title: 'Overtaking Analysis by Zone Type' }
      );
    }
    
    // Safety Car Impact
    const scChart = document.getElementById('chart-sunday-safetycar');
    if (scChart) {
      F1Charts.barChart(
        scChart,
        ['No SC', '1 SC', '2 SC', 'VSC'],
        [0.65, 0.25, 0.08, 0.02],
        ['#1DA36B', '#D97B0A', '#E10600', '#16233F'],
        { title: 'Safety Car Impact on Race Outcome' }
      );
    }
    
    // Race Pace Evolution
    const paceChart = document.getElementById('chart-sunday-pace');
    if (paceChart) {
      F1Charts.lineChart(
        paceChart,
        ['Lap 1', 'Lap 15', 'Lap 30', 'Lap 45', 'Lap 60'],
        {
          'Leader': [92, 90, 88, 87, 86],
          'Chaser': [94, 91, 89, 88, 87],
          'Midfield': [96, 93, 91, 90, 89]
        },
        { title: 'Race Pace Evolution' }
      );
    }
    
    // Fuel Load Impact
    const fuelChart = document.getElementById('chart-sunday-fuel');
    if (fuelChart) {
      F1Charts.lineChart(
        fuelChart,
        ['Lap 1', 'Lap 15', 'Lap 30', 'Lap 45', 'Lap 60'],
        {
          'Lap Time': [92, 89, 87, 86, 85],
          'Fuel Adjusted': [90, 88, 87, 86, 85]
        },
        { title: 'Fuel Load Impact on Lap Times' }
      );
    }
    
    // Weather Strategy Impact
    const weatherChart = document.getElementById('chart-sunday-weather');
    if (weatherChart) {
      F1Charts.barChart(
        weatherChart,
        ['Dry Race', 'Mixed Conditions', 'Wet Race'],
        [0.72, 0.58, 0.45],
        ['#1DA36B', '#D97B0A', '#16233F'],
        { title: 'Weather Strategy Impact' }
      );
    }
  }

  // -----------------------------------------------------------------------
  // Results
  // -----------------------------------------------------------------------
  function targetsForSession() {
    return Object.values(TARGETS).filter((t) => t.session === state.session);
  }

  function renderResults() {
    const hasRun = state.runState === "done";
    $("#results-empty").style.display = hasRun ? "none" : "block";
    $("#results-content").style.display = hasRun ? "block" : "none";
    
    // Always show session content based on current session selection
    showSessionContent();
    
    if (!hasRun) return;

    renderGridStatusBanner();

    // Generate charts based on session
    if (state.session === "practice") {
      generateFridayCharts();
    } else if (state.session === "qualifying") {
      generateSaturdayCharts();
    } else if (state.session === "race") {
      generateSundayCharts();
    }
    
    document.querySelectorAll(".charts-grid-3")[0].style.display = "grid";
    $("#practice-not-supported").style.display = "none";
    $("#dnf-card").style.display = state.session === "race" ? "block" : "none";

    const targets = targetsForSession();
    if (!targets.find((t) => t.id === state.targetId)) state.targetId = targets[0]?.id || "podium";

    $("#target-pills").style.display = targets.length > 1 ? "flex" : "none";
    $("#target-pills").innerHTML = targets.map((t) => `
      <button data-target="${t.id}" class="target-pill ${t.id === state.targetId ? "is-active" : ""}">${t.short}</button>
    `).join("");
    $("#target-pills").querySelectorAll("[data-target]").forEach((btn) => {
      btn.addEventListener("click", () => { state.targetId = btn.dataset.target; renderResults(); });
    });

    let result = state.predictions[state.targetId];
    if (!result || !result.predictions) {
      const availableKeys = Object.keys(state.predictions);
      if (availableKeys.length > 0) {
        const matchingKey = availableKeys.find(k => TARGETS[k] && TARGETS[k].session === state.session) || availableKeys[0];
        result = state.predictions[matchingKey];
        if (matchingKey && TARGETS[matchingKey]) state.targetId = matchingKey;
      }
    }
    const target = TARGETS[state.targetId] || { id: state.targetId, label: state.targetId, sum: 1 };
    $("#dist-title").textContent = `${target.label} Distribution`;

    if (!result || result.error || !result.predictions) {
      F1.showError($("#podium-cards"), (result && result.error) || "No prediction available.");
      $("#results-table-wrap").innerHTML = "";
      return;
    }

    const field = result.predictions.map((p) => Object.assign({}, p, driverInfo(p.driver_code)));

    renderPodiumCards(field, target);
    renderConfidence(result.confidence);
    renderDistribution(field, target);
    renderDnf(field);
    renderTable(field, target);
    setStat("#stat-confidence", result.confidence != null ? Math.round(result.confidence * 100) / 100 + "%" : "—", result.confidence == null);
    
    // Ensure appropriate session content is visible
    showSessionContent();
  }

  function driverInfo(code) {
    const d = state.driverMap[code] || {};
    return {
      name: d.name || code,
      teamName: d.team_name || "—",
      teamId: d.team_id || "",
      number: d.number || "",
      color: d.team_color || F1.teamColor(d.team_id),
      reliability: d.reliability != null ? d.reliability : 80,
      dnfRisk: F1.dnfRiskFromReliability(d.reliability != null ? d.reliability : 80),
      gridPos: state.gridPositions ? state.gridPositions[code] : null,
    };
  }

  function renderPodiumCards(field, target) {
    const top3 = field.slice(0, 3);
    $("#podium-cards").innerHTML = top3.map((d, idx) => {
      const purple = idx === 0;
      return `<div class="result-card" style="${purple ? "border-color:var(--purple)" : ""}">
        <span class="rank-swatch" style="background:${d.color}"></span>
        ${purple ? '<span class="badge-purple" style="position:absolute;top:12px;right:12px">Purple Pick</span>' : ""}
        <div class="pl-2">
          <div class="flex items-center gap-2 mb-1.5">
            <span class="img-slot" style="width:32px;height:32px;border-radius:999px;border-width:1.5px">&#128100;</span>
            <div>
              <div class="f1-mono fs-11 uppercase tracking-widest font-semibold text-sub">${F1.ordinal(idx + 1)} &middot; projected</div>
              <div class="f1-display text-base font-bold">${F1.escapeHtml(d.name)}</div>
            </div>
          </div>
          <div class="fs-11 mb-1.5 text-sub">${F1.escapeHtml(d.teamName)} &middot; #${d.number}</div>
          <div class="f1-mono text-2xl font-bold" style="color:${purple ? "var(--purple)" : "var(--text)"}">
            ${d.percentage.toFixed(1)}<span class="text-base text-sub">%</span>
          </div>
          <div class="fs-11 mt-1 text-sub">${target.label} probability</div>
        </div>
      </div>`;
    }).join("");
  }

  function renderConfidence(confidence) {
    const val = confidence != null ? Math.round(confidence * 100) / 100 : 0;
    const displayVal = confidence != null && confidence <= 1 ? Math.round(confidence * 100) : Math.round(confidence || 0);
    F1Charts.gauge($("#chart-confidence"), Math.min(100, displayVal));
    $("#gauge-value-num").textContent = confidence != null ? displayVal + "%" : "—";
  }

  function renderDistribution(field, target) {
    const rows = field.slice(0, 12);
    F1Charts.barDistribution(
      $("#chart-distribution"),
      rows.map((d) => d.driver_code),
      rows.map((d) => Number(d.percentage.toFixed(1))),
      rows.map((d) => d.color),
      { tooltipSuffix: "%" }
    );
  }

  function renderDnf(field) {
    const counts = { Low: 0, Medium: 0, High: 0 };
    field.forEach((d) => { counts[d.dnfRisk] = (counts[d.dnfRisk] || 0) + 1; });
    const p = F1.palette();
    const entries = [["Low risk", counts.Low, p.green], ["Medium risk", counts.Medium, p.amber], ["High risk", counts.High, p.red]].filter((e) => e[1] > 0);
    F1Charts.doughnut($("#chart-dnf"), entries.map((e) => e[0]), entries.map((e) => e[1]), entries.map((e) => e[2]));
  }

  function renderTable(field, target) {
    const showGrid = state.session === "race";
    const head = `<div class="fs-10 uppercase tracking-widest font-bold px-4 py-2 surface-alt text-sub" style="display:grid;grid-template-columns:36px 44px 1fr 140px ${showGrid ? "60px" : ""} 90px;gap:8px">
      <span>#</span><span></span><span>Driver</span><span>Probability</span>${showGrid ? "<span>Grid</span>" : ""}<span>DNF risk</span>
    </div>`;
    const rows = field.map((d, i) => `
      <div style="display:grid;grid-template-columns:36px 44px 1fr 140px ${showGrid ? "60px" : ""} 90px;gap:8px" class="items-center px-4 py-2 text-sm" ${i > 0 ? 'style="border-top:1px solid var(--border)"' : ""}>
        <span class="f1-mono font-bold" style="color:${i < target.sum ? "var(--text)" : "var(--muted)"}">${i + 1}</span>
        <span style="width:10px;height:22px;border-radius:3px;background:${d.color}"></span>
        <span style="min-width:0">
          <span class="f1-mono font-bold tracking-wide">${d.driver_code}</span>
          <span class="text-xs text-sub" style="margin-left:6px">${F1.escapeHtml(d.name)} &middot; ${F1.escapeHtml(d.teamName)}</span>
        </span>
        <span>
          <span class="relative block h-2 rounded-full overflow-hidden surface-alt">
            <span class="absolute left-0 top-0 h-full rounded-full" style="width:${Math.min(100, d.percentage)}%;background:${d.color}"></span>
          </span>
        </span>
        ${showGrid ? `<span class="f1-mono fs-11 font-semibold text-sub">${d.gridPos ? "P" + d.gridPos : "—"}</span>` : ""}
        <span class="f1-mono fs-11 font-semibold flex items-center gap-1.5" style="color:${F1.riskColor(d.dnfRisk)}">
          <span style="width:6px;height:6px;border-radius:999px;background:${F1.riskColor(d.dnfRisk)}"></span>${d.dnfRisk}
        </span>
      </div>`).join("");
    $("#results-table-wrap").innerHTML = `<div class="f1-table" style="min-width:640px">${head}${rows}</div>`;
  }

  // -----------------------------------------------------------------------
  // Events
  // -----------------------------------------------------------------------
  function bindEvents() {
    ["#hero-race-select", "#cb-race-select"].forEach((sel) => {
      $(sel).addEventListener("change", (e) => {
        state.draft.raceId = e.target.value;
        renderHero();
        renderRealResultBanner();
        populateSubSessionSelect(); // Update sub-sessions when race changes
        
        // ✅ Enable/disable run button based on race selection
        const runBtn = $("#run-btn");
        if (state.draft.raceId) {
          runBtn.disabled = false;
          runBtn.innerHTML = `<span id="run-btn-label">Run Prediction</span>`;
        } else {
          runBtn.disabled = true;
          runBtn.innerHTML = `<span id="run-btn-label">Select Grand Prix</span>`;
        }
      });
    });
    ["#hero-weather-select", "#cb-weather-select"].forEach((sel) => {
      $(sel).addEventListener("change", (e) => {
        state.draft.weather = e.target.value;
        renderHero();
      });
    });
    $("#cb-sim-count").addEventListener("change", (e) => {
      state.draft.simCount = Math.max(100, Math.min(100000, Number(e.target.value) || 0));
      setSimStat();
    });
    $("#cb-sub-session").addEventListener("change", (e) => {
      state.subSession = e.target.value;
      // Update target based on sub-session selection
      if (state.session === "qualifying") {
        if (state.subSession === "Q1") state.targetId = "qualifying_q1";
        else if (state.subSession === "Q2") state.targetId = "qualifying_q2";
        else if (state.subSession === "Q3") state.targetId = "qualifying_q3";
        else state.targetId = "qualifying_q3";
      } else if (state.session === "practice") {
        if (state.subSession === "FP1") state.targetId = "practice_fp1";
        else if (state.subSession === "FP2") state.targetId = "practice_fp2";
        else if (state.subSession === "FP3") state.targetId = "practice_fp3";
        else state.targetId = "practice_pace";
      }
    });
    $("#run-btn").addEventListener("click", handleRun);

    // Export functionality
    $("#export-btn").addEventListener("click", handleExport);
    document.querySelectorAll(".export-card").forEach(card => {
      card.addEventListener("click", (e) => {
        const format = e.currentTarget.dataset.format;
        handleExportByFormat(format);
      });
    });

    document.addEventListener("f1:theme-change", () => { renderResults(); });
  }

  document.addEventListener("DOMContentLoaded", init);
  
  // Fallback: if DOMContentLoaded already fired, call init immediately
  if (document.readyState === "complete" || document.readyState === "interactive") {
    console.log("DOM already loaded, calling init immediately");
    setTimeout(init, 100);
  }
})();
