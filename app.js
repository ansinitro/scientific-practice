// Scientific Practice Defense Portal JS Controller

// ==========================================
// 1. Core State & Data Registries
// ==========================================

const ARCHIVE_MODELS = [
    {
        name: "FastConformer Kazakh",
        type: "Conformer-CTC",
        parameters: "115M",
        dataset: "Kazakh Speech MFA (400h)",
        wer_pure: "9.2%",
        wer_shala: "24.5%",
        rtf: 0.08,
        license: "Apache 2.0 (Free)",
        notes: "Highly optimized for formal Kazakh speech, Struggles on Shala-Kazakh code-switching.",
        status: "Validated"
    },
    {
        name: "Soyle Kazakh Speech",
        type: "Sequence-to-Sequence ONNX",
        parameters: "85M",
        dataset: "AITU Speech (250h)",
        wer_pure: "11.4%",
        wer_shala: "19.8%",
        rtf: 0.05,
        license: "Non-commercial (Restrict)",
        notes: "Excellent on shala-kazakh colloquialisms due to custom sequence normalization.",
        status: "Validated"
    },
    {
        name: "Whisper-large-v3 (Fine-tuned)",
        type: "Transformer Sequence-to-Sequence",
        parameters: "1.5B",
        dataset: "Finetuned on CommonVoice 15 + MFA",
        wer_pure: "4.8%",
        wer_shala: "12.3%",
        rtf: 0.85,
        license: "MIT (Free)",
        notes: "State-of-the-art accuracy. Extremely heavy; requires high-end GPU accelerator.",
        status: "R&D Complete"
    },
    {
        name: "MMS-1B-All Kazakh",
        type: "Wav2Vec 2.0 Adapter",
        parameters: "1.0B",
        dataset: "Multilingual MFA (Kazakh Split)",
        wer_pure: "14.2%",
        wer_shala: "32.1%",
        rtf: 0.18,
        license: "CC-BY-NC 4.0 (Restrict)",
        notes: "Meta AI's massive multilingual model. Average adaptation for colloquial speech.",
        status: "Discarded"
    },
    {
        name: "QuartzNet Kazakh",
        type: "1D CNN-CTC",
        parameters: "19M",
        dataset: "Kazakh Speech MFA (400h)",
        wer_pure: "16.8%",
        wer_shala: "38.5%",
        rtf: 0.03,
        license: "Apache 2.0 (Free)",
        notes: "Lightweight candidate. Fast CPU inference but subpar vocabulary depth.",
        status: "Baseline"
    }
];

// Task 3: Extracted Filler Word & Interjections Data
const FILLER_CATEGORIES = {
    discourse: [
        { word: "ал", count: 11145, details: "Introduces sentences, acts as a coordinator ('and', 'now')" },
        { word: "сол", count: 10310, details: "Literal: 'that'. Used widely as a verbal delay placeholder" },
        { word: "енді", count: 5923, details: "Literal: 'now'. Transitional pause word" },
        { word: "жалпы", count: 4441, details: "Literal: 'in general'. Fill word when structuralizing ideas" },
        { word: "сондықтан", count: 4008, details: "Literal: 'therefore'. Often repeated without semantic clause connection" },
        { word: "яғни", count: 2510, details: "Literal: 'meaning / i.e.'. Frequently repeated placeholder" },
        { word: "міне", count: 1339, details: "Literal: 'here'. Discourse pointing word" },
        { word: "әрине", count: 1299, details: "Literal: 'of course'. Pragmatic filler particle" },
        { word: "айталық", count: 98, details: "Literal: 'let's say'. Hypothetical filler pause" }
    ],
    expressive: [
        { word: "ай", count: 1792, details: "Expresses grief, mild frustration, or calling attention" },
        { word: "ой", count: 1397, details: "Universal exclamation of regret, surprise, or contemplation" },
        { word: "е", count: 384, details: "Vocal confirmation, understanding, or casual delay" },
        { word: "әй", count: 307, details: "Informal attention drawer or exclamation" },
        { word: "қап", count: 294, details: "Interjection of regret ('dammit')" },
        { word: "ә", count: 211, details: "Query particle or expression of mild surprise" },
        { word: "м", count: 155, details: "Agreement murmur or cognitive delay sound" },
        { word: "ойбай", count: 115, details: "Heavy exclamation of shock, distress, or surprise" },
        { word: "шүкір", count: 108, details: "Expression of gratitude / relief ('thank goodness')" },
        { word: "қарашы", count: 82, details: "Literal: 'look'. Interjection used to emphasize a claim" },
        { word: "тоқта", count: 42, details: "Literal: 'stop'. Used as cognitive halt interjection" }
    ],
    non_lexical: [
        { word: "ыыы", count: 811, details: "Prolonged hesitative hum (Kazakh spelling of 'uh / um')" },
        { word: "ііі", count: 388, details: "Vocalized guttural hesitation particle specific to Kazakh phonemes" },
        { word: "ммм", count: 171, details: "Nasalized prolonged hesitation murmur" },
        { word: "эээ", count: 17, details: "Vowel vocalization delay sound" },
        { word: "мм", count: 17, details: "Short nasalized pause" },
        { word: "ссср", count: 29, details: "Non-lexical artifact originating from manual labeling typo in source" }
    ]
};

// ==========================================
// 2. Global DOM Router & Lifecycle
// ==========================================

document.addEventListener("DOMContentLoaded", () => {
    // 1. Setup Tab Switching Router
    setupNavigation();
    
    // 2. Initialize Task 1 View (Model Pool)
    renderModelPool();
    setupSearchFilters();
    
    // 3. Initialize Task 2 View (STT Karaoke Benchmark)
    initializeSTTBenchmark();
    
    // 4. Initialize Task 3 View (Filler Dataset Preprocessing Explorer)
    renderFillerData('discourse');
    
    // 5. Initialize Task 5 Audio Players (TTS Showcase)
    setupTTSPlayground();
});

function setupNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    const sections = document.querySelectorAll(".view-section");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const targetView = item.getAttribute("data-view");
            
            navItems.forEach(n => n.classList.remove("active"));
            sections.forEach(s => s.classList.remove("active"));
            
            item.classList.add("active");
            const targetEl = document.getElementById(`view-${targetView}`);
            if (targetEl) {
                targetEl.classList.add("active");
            }
            
            // Special trigger: pause benchmark video if leaving STT tab
            const videoPlayer = document.getElementById("stt-video-player");
            if (targetView !== "stt-benchmark" && videoPlayer) {
                videoPlayer.pause();
            }
        });
    });
}

// ==========================================
// 3. Task 1: Model Pool Registry Logic
// ==========================================

function renderModelPool(filterQuery = "") {
    const tbody = document.getElementById("model-pool-tbody");
    if (!tbody) return;
    
    tbody.innerHTML = "";
    
    const filtered = ARCHIVE_MODELS.filter(m => {
        const query = filterQuery.toLowerCase();
        return m.name.toLowerCase().includes(query) || 
               m.type.toLowerCase().includes(query) ||
               m.dataset.toLowerCase().includes(query);
    });
    
    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted);">No models found matching your search.</td></tr>`;
        return;
    }
    
    filtered.forEach(m => {
        const tr = document.createElement("tr");
        
        let licenseClass = "badge-license";
        if (m.license.includes("Free")) licenseClass += " free";
        else if (m.license.includes("Restrict")) licenseClass += " restrict";
        
        tr.innerHTML = `
            <td style="font-weight:700; color:var(--text-main);">${m.name}</td>
            <td><span style="font-family:'Outfit'; font-size:0.8rem; font-weight:600; color:#3b82f6;">${m.type}</span></td>
            <td style="font-family:'JetBrains Mono';">${m.parameters}</td>
            <td style="font-size:0.8rem; color:var(--text-secondary);">${m.dataset}</td>
            <td style="font-family:'JetBrains Mono'; font-weight:700; color:#10b981;">${m.wer_pure} / <span style="color:#fb923c;">${m.wer_shala}</span></td>
            <td><span class="${licenseClass}">${m.license}</span></td>
            <td style="font-size:0.75rem; color:var(--text-muted); font-style:italic;">${m.notes}</td>
        `;
        tbody.appendChild(tr);
    });
}

function setupSearchFilters() {
    const searchInput = document.getElementById("model-search");
    if (searchInput) {
        searchInput.addEventListener("input", (e) => {
            renderModelPool(e.target.value);
        });
    }
}

// ==========================================
// 4. Task 2: Speech Benchmarking Portal (Karaoke subtitle sync)
// ==========================================

let sttCurrentData = null;
const STT_MODELS = ['fastconformer', 'quartznet', 'soyle', 'whisper-turbo'];
const STT_MODEL_CLASSES = {
    'fastconformer': 'fastconformer',
    'quartznet': 'quartznet',
    'soyle': 'soyle',
    'whisper-turbo': 'whisper'
};
const STT_MODEL_NAMES = {
    'fastconformer': 'FastConformer',
    'quartznet': 'QuartzNet',
    'soyle': 'Soyle ONNX',
    'whisper-turbo': 'Whisper-Turbo'
};

function initializeSTTBenchmark() {
    const player = document.getElementById("stt-video-player");
    if (!player) return;
    
    if (typeof ALIGNED_DATA === "undefined") {
        console.warn("ALIGNED_DATA not loaded in global context.");
        return;
    }
    
    renderSTTPlaylist();
    loadSTTVideo(ALIGNED_DATA[0]); // Load first benchmark video by default
    
    player.addEventListener("timeupdate", handleSTTTimeUpdate);
}

function renderSTTPlaylist() {
    const container = document.getElementById("stt-playlist");
    if (!container) return;
    
    container.innerHTML = "";
    
    ALIGNED_DATA.forEach((item, index) => {
        const div = document.createElement("div");
        div.className = "eval-play-item" + (index === 0 ? " active" : "");
        
        const cleanName = item.audio.replace(".mp3", "").replace(/_/g, " ");
        const isShala = item.dataset === "shala_audio";
        const badge = isShala 
            ? `<span style="font-size:0.6rem; font-weight:700; text-transform:uppercase; padding:1px 6px; border-radius:3px; background:rgba(249,115,22,0.15); color:#fb923c; border:1px solid rgba(249,115,22,0.25);">Shala</span>`
            : `<span style="font-size:0.6rem; font-weight:700; text-transform:uppercase; padding:1px 6px; border-radius:3px; background:rgba(16,185,129,0.15); color:#34d399; border:1px solid rgba(16,185,129,0.25);">Pure</span>`;
            
        div.innerHTML = `
            <div>
                <div class="eval-item-title" title="${item.audio}">${cleanName.charAt(0).toUpperCase() + cleanName.slice(1)}</div>
                <div style="margin-top:4px; display:flex; gap:6px; align-items:center;">
                    ${badge}
                    <span class="eval-item-duration">${item.duration.toFixed(1)}s</span>
                </div>
            </div>
            <span class="nav-item-icon">▶</span>
        `;
        
        div.onclick = () => {
            document.querySelectorAll(".eval-play-item").forEach(el => el.classList.remove("active"));
            div.classList.add("active");
            loadSTTVideo(item);
        };
        
        container.appendChild(div);
    });
}

function loadSTTVideo(videoData) {
    sttCurrentData = videoData;
    const player = document.getElementById("stt-video-player");
    if (!player) return;
    
    // IMPORTANT: resolve the video path relative to the root catalog where main index.html lives
    // Since video paths inside results_aligned.js are relative to 02_models_test/
    player.src = "02_models_test/" + videoData.video;
    
    // Render the micro metrics dashboard
    renderSTTMetrics(videoData);
    
    // Render the interactive transcripts
    renderSTTTranscripts(videoData);
    
    // Render the alignment matrix table
    renderSTTMatrix(videoData);
    
    // Reset Subtitles
    resetSTTSubtitles();
}

function renderSTTMetrics(videoData) {
    const container = document.getElementById("stt-metrics-grid");
    if (!container) return;
    
    container.innerHTML = "";
    
    STT_MODELS.forEach(model => {
        const mData = videoData.models[model];
        const rtf = mData.rtf ? mData.rtf.toFixed(4) : "N/A";
        const speedup = mData.rtf ? (1 / mData.rtf).toFixed(1) : "N/A";
        const wClass = STT_MODEL_CLASSES[model];
        
        const box = document.createElement("div");
        box.className = "mini-metric-item";
        box.innerHTML = `
            <div style="font-family:'Outfit'; font-size:0.75rem; font-weight:700; display:flex; align-items:center; justify-content:center; gap:6px; margin-bottom:4px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--color-${wClass})"></span>
                ${STT_MODEL_NAMES[model]}
            </div>
            <div class="mini-metric-num" style="color:var(--color-${wClass});">${speedup}x</div>
            <div class="mini-metric-lbl">RTF: ${rtf}</div>
        `;
        container.appendChild(box);
    });
}

function renderSTTTranscripts(videoData) {
    STT_MODELS.forEach(model => {
        const container = document.getElementById(`sub-${model === 'whisper-turbo' ? 'whisper' : model}`);
        if (!container) return;
        
        container.innerHTML = "";
        
        const mData = videoData.models[model];
        if (!mData.words || mData.words.length === 0) {
            container.innerHTML = `<span class="empty">No speech words detected.</span>`;
            return;
        }
        
        mData.words.forEach((wordObj, idx) => {
            const span = document.createElement("span");
            span.className = "eval-word";
            span.textContent = wordObj.text;
            span.dataset.start = wordObj.start;
            span.dataset.end = wordObj.end;
            span.dataset.index = idx;
            span.onclick = () => {
                const player = document.getElementById("stt-video-player");
                if (player) {
                    player.currentTime = wordObj.start + 0.05;
                    player.play();
                }
            };
            container.appendChild(span);
            container.appendChild(document.createTextNode(" "));
        });
    });
}

function renderSTTMatrix(videoData) {
    const container = document.getElementById("stt-matrix-tbody");
    if (!container) return;
    
    container.innerHTML = "";
    
    const whisperData = videoData.models["whisper-turbo"];
    if (!whisperData.segments || whisperData.segments.length === 0) {
        container.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No segments available for comparison.</td></tr>`;
        return;
    }
    
    whisperData.segments.forEach(refSeg => {
        const tr = document.createElement("tr");
        tr.dataset.start = refSeg.start;
        tr.dataset.end = refSeg.end;
        
        // Time Cell
        const timeCell = document.createElement("td");
        timeCell.innerHTML = `
            <span style="font-family:'JetBrains Mono'; font-weight:700; color:#3b82f6; cursor:pointer;" onclick="const pl = document.getElementById('stt-video-player'); pl.currentTime = ${refSeg.start}; pl.play();">
                ${refSeg.start.toFixed(1)}s - ${refSeg.end.toFixed(1)}s
            </span>
        `;
        tr.appendChild(timeCell);
        
        // Model columns
        STT_MODELS.forEach(model => {
            const td = document.createElement("td");
            const mData = videoData.models[model];
            
            // Filter words inside time window
            const segWords = mData.words
                .filter(w => w.start >= refSeg.start - 0.5 && w.start <= refSeg.end + 0.5)
                .map(w => w.text);
                
            td.textContent = segWords.length > 0 ? segWords.join(" ") : "...";
            tr.appendChild(td);
        });
        
        container.appendChild(tr);
    });
}

function resetSTTSubtitles() {
    STT_MODELS.forEach(model => {
        const words = document.querySelectorAll(`#sub-${model === 'whisper-turbo' ? 'whisper' : model} .eval-word`);
        words.forEach(w => w.classList.remove("active", "active-fastconformer", "active-quartznet", "active-soyle", "active-whisper"));
    });
}

function handleSTTTimeUpdate() {
    if (!sttCurrentData) return;
    
    const player = document.getElementById("stt-video-player");
    if (!player) return;
    
    const time = player.currentTime;
    
    // Highlight Words inside the comparative subtitle viewer and center-scroll
    STT_MODELS.forEach(model => {
        const container = document.getElementById(`sub-${model === 'whisper-turbo' ? 'whisper' : model}`);
        if (!container) return;
        
        const words = container.querySelectorAll(".eval-word");
        const mClass = STT_MODEL_CLASSES[model];
        
        let activeEl = null;
        
        words.forEach(wordEl => {
            const start = parseFloat(wordEl.dataset.start);
            const end = parseFloat(wordEl.dataset.end);
            const isActive = time >= start && time <= end;
            
            wordEl.classList.remove("active", "active-fastconformer", "active-quartznet", "active-soyle", "active-whisper");
            
            if (isActive) {
                wordEl.classList.add("active", `active-${mClass}`);
                activeEl = wordEl;
            }
        });
        
        // Center scroll active word horizontally inside display box
        if (activeEl) {
            const parent = container;
            const parentWidth = parent.clientWidth;
            const wordLeft = activeEl.offsetLeft;
            const wordWidth = activeEl.clientWidth;
            
            parent.scrollLeft = wordLeft - (parentWidth / 2) + (wordWidth / 2);
        }
    });
    
    // Highlight Row inside Matrix
    const rows = document.querySelectorAll("#stt-matrix-tbody tr");
    rows.forEach(row => {
        const start = parseFloat(row.dataset.start);
        const end = parseFloat(row.dataset.end);
        
        if (time >= start && time <= end) {
            row.style.background = "rgba(59, 130, 246, 0.08)";
            row.style.color = "var(--text-main)";
        } else {
            row.style.background = "";
            row.style.color = "";
        }
    });
}

// ==========================================
// 5. Task 3: Filler Dataset Explorer
// ==========================================

function selectFillerCategory(category, element) {
    document.querySelectorAll(".filler-pill").forEach(el => el.classList.remove("active"));
    element.classList.add("active");
    renderFillerData(category);
}

function renderFillerData(category) {
    const list = FILLER_CATEGORIES[category] || [];
    const container = document.getElementById("filler-word-list");
    if (!container) return;
    
    container.innerHTML = "";
    
    if (list.length === 0) {
        container.innerHTML = `<div style="color:var(--text-muted); text-align:center; padding:20px;">No fillers in this category.</div>`;
        return;
    }
    
    list.forEach(item => {
        const row = document.createElement("div");
        row.style.display = "flex";
        row.style.justifyContent = "space-between";
        row.style.alignItems = "center";
        row.style.background = "rgba(255, 255, 255, 0.015)";
        row.style.border = "1px solid rgba(255, 255, 255, 0.03)";
        row.style.borderRadius = "8px";
        row.style.padding = "12px 16px";
        row.style.transition = "all 0.2s ease";
        
        row.onmouseover = () => row.style.borderColor = "rgba(16, 185, 129, 0.25)";
        row.onmouseout = () => row.style.borderColor = "rgba(255, 255, 255, 0.03)";
        
        row.innerHTML = `
            <div>
                <span style="font-family:'Outfit'; font-weight:700; font-size:1.1rem; color:#10b981; margin-right:12px;">${item.word}</span>
                <span style="font-size:0.78rem; color:var(--text-secondary);">${item.details}</span>
            </div>
            <div style="text-align:right;">
                <span style="font-family:'JetBrains Mono'; font-weight:700; font-size:0.95rem; color:var(--text-main);">${item.count}</span>
                <div style="font-size:0.6rem; color:var(--text-muted); text-transform:uppercase;">Occurrences</div>
            </div>
        `;
        container.appendChild(row);
    });
}

// ==========================================
// 6. Task 5: TTS Playground & Audio Player
// ==========================================

const TTS_AUDIO_SAMPLES = [
    {
        id: "piper-samaya",
        title: "Казахский TTS (Короткий)",
        phrase: "Самая вышка",
        path: "05_kazakh_tts/results/piper_kk_samaya.wav",
        desc: "Базовый образец ONNX-модели с быстрой генерацией гласных."
    },
    {
        id: "piper-vyshka",
        title: "Казахский TTS (Полный)",
        phrase: "Самая вышка, десе де болады",
        path: "05_kazakh_tts/results/piper_samaya_vyshka.wav",
        desc: "Демонстрация плавного сопряжения согласных в длинной синтагме."
    },
    {
        id: "piper-gg",
        title: "Интерактивный Тест (GG)",
        phrase: "Джи-джи",
        path: "05_kazakh_tts/results/piper_gg.wav",
        desc: "ONNX генератор для фонетического анализа латинских аббревиатур."
    }
];

let activeAudioElement = null;
let activeVisualizer = null;
let activePlayBtn = null;

function setupTTSPlayground() {
    const list = document.getElementById("tts-samples-list");
    if (!list) return;
    
    list.innerHTML = "";
    
    TTS_AUDIO_SAMPLES.forEach(sample => {
        const card = document.createElement("div");
        card.className = "tts-card";
        
        card.innerHTML = `
            <div class="tts-meta">
                <span class="tts-title">${sample.title}</span>
                <span class="tts-phrase">Текст: "${sample.phrase}"</span>
                <span style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">${sample.desc}</span>
            </div>
            
            <div style="display:flex; align-items:center; gap:20px;">
                <div class="audio-visualizer" id="viz-${sample.id}">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
                
                <button class="tts-control-btn" id="btn-${sample.id}">▶</button>
            </div>
        `;
        
        const btn = card.querySelector(`#btn-${sample.id}`);
        const viz = card.querySelector(`#viz-${sample.id}`);
        
        // Setup internal audio object
        const audio = new Audio(sample.path);
        
        btn.onclick = () => {
            // If clicking active playing audio: pause it
            if (activeAudioElement === audio) {
                if (audio.paused) {
                    audio.play();
                    btn.textContent = "⏸";
                    viz.classList.add("playing");
                } else {
                    audio.pause();
                    btn.textContent = "▶";
                    viz.classList.remove("playing");
                }
            } else {
                // Clicking new audio
                if (activeAudioElement) {
                    activeAudioElement.pause();
                    activeAudioElement.currentTime = 0;
                    if (activePlayBtn) activePlayBtn.textContent = "▶";
                    if (activeVisualizer) activeVisualizer.classList.remove("playing");
                }
                
                audio.play();
                btn.textContent = "⏸";
                viz.classList.add("playing");
                
                activeAudioElement = audio;
                activePlayBtn = btn;
                activeVisualizer = viz;
            }
        };
        
        audio.onended = () => {
            btn.textContent = "▶";
            viz.classList.remove("playing");
            activeAudioElement = null;
            activePlayBtn = null;
            activeVisualizer = null;
        };
        
        list.appendChild(card);
    });
}
