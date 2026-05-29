# 🎙️ Kazakh Speech Technologies (STT & TTS)
**Scientific Practice Defense Project**

A comprehensive, interactive research repository exploring state-of-the-art **Automatic Speech Recognition (ASR)** and **Text-to-Speech (TTS)** technologies optimized for the Kazakh language. This project tackles the unique challenges of colloquial code-switching (*Shala-Kazakh*) and extreme low-latency voice synthesis.

---

## 🚀 The Defense Portal
This repository contains a **zero-dependency Single Page Application (SPA)** that acts as an interactive presentation portal. It visually demonstrates the empirical findings and datasets generated during this 5-task scientific practice.

### How to Run the Portal
You can launch the interactive portal locally by spinning up a simple HTTP server to avoid browser CORS restrictions on media files.

```bash
# Clone the repository
git clone https://github.com/ansinitro/scientific-practice.git
cd scientific-practice

# Start a local web server (Python 3)
python3 -m http.server 8080

# Open your browser and navigate to:
http://localhost:8080/index.html
```

---

## 🔬 Research Tasks Completed

### Task 1: STT Model Candidate Pool
Cataloged and evaluated the current landscape of Kazakh ASR models (e.g., *Whisper-large-v3, FastConformer, Soyle ONNX, QuartzNet, MMS-1B*). Analysed architectural differences, parameter scales, dataset dependencies, and commercial licensing.

### Task 2: Live Speech Benchmarking & Dialect Analysis
Developed a karaoke-style subtitle synchronizer to benchmark real-time transcription speeds (RTF) and Word Error Rates (WER). 
* **Key Finding:** Standard models (like FastConformer) experience a massive **15-20% drop in accuracy** when exposed to *Shala-Kazakh* (code-switched Russian/Kazakh colloquialisms) compared to formal Pure-Kazakh.

### Task 3: Acoustic Dataset Preprocessing (Filler Extraction)
Processed a **408,010-sample** speech dataset to prepare it for high-fidelity TTS training.
* Extracted and categorized **37,000+ Discourse Fillers** (e.g., *'ал', 'сол'*).
* Classified **4,900+ Expressive Interjections** (e.g., *'ойбай'*).
* Pruned non-lexical hesitations (*'ыыы'*) to prevent TTS hallucinations.

### Tasks 4 & 5: TTS Architecture & Low-Latency Deployment
Researched the architectural shift from autoregressive models to **Flow Matching** and **Diffusion** transformers (e.g., F5-TTS). 
* Deployed optimized **ONNX** voice synthesis models utilizing the Piper TTS engine.
* Successfully generated highly natural Kazakh speech with an ultra-low start latency of **<50 milliseconds** running locally.

---

## 🛠️ Tech Stack & Directory Structure
* **Frontend Portal:** Vanilla HTML5, CSS3 (Glassmorphism UI), JavaScript.
* **Data Processing:** Python (Pandas, PyTorch, Transformers, ONNX Runtime).
* **`/01_find_models`** - STT Model registry and architectural notes.
* **`/02_models_test`** - Video/Audio benchmark data and alignment scripts.
* **`/03_dataset_preprocessing`** - Jupyter notebooks for regex token pruning.
* **`/04_STT_chetam`** - TTS Research and Flow Matching pipeline diagrams.
* **`/05_kazakh_tts`** - ONNX voice weights and synthetic audio results.

---

**Author:** Ansinitro  
**Context:** Scientific Practice Defense  
**Domain:** Artificial Intelligence / Speech Technologies
