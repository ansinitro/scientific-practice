# %% [markdown]
# # Filler and Interjection Candidate Extraction Pipeline
# This notebook processes the `govnejri/kazakh_speech_mfa_punctuation` dataset to prepare a word-level cleaning pipeline for fine-tuning Microsoft VibeVoice TTS.
# 
# ## Part 1 - Candidate Extraction & Auto-Labelling

# %%
import os

# Create results directory
os.makedirs("results", exist_ok=True)

# Set Hugging Face cache location
os.environ["HF_HOME"] = "/media/storage/huggingface"
os.environ["HF_DATASETS_CACHE"] = "/media/storage/huggingface/datasets"

import json
import re
import base64
import io
import wave
import numpy as np
from datasets import load_dataset, Audio
from collections import defaultdict

# 1.1 Load dataset
print("Loading dataset...")

ds = load_dataset(
    "govnejri/kazakh_speech_mfa_punctuation",
    split="train",
    cache_dir="/media/storage/huggingface",
    verification_mode="no_checks"
)

# Fix: Prevent Hugging Face from crashing on audio decode if 'torchcodec' is missing
if "audio" in ds.features and getattr(ds.features["audio"], "decode", True):
    ds = ds.cast_column("audio", Audio(decode=False))

print(f"Loaded {len(ds)} samples.")

# %%
# 1.2 Hard-coded word lists
HESITATION_FILLERS = {
    'іі', 'мм', 'уу', 'аа', 'әә', 'ээ', 'оо', 'һһ', 'ыы'
}

DISCOURSE_FILLERS = {
    'яғни', 'сол', 'ал', 'енді', 'міне', 'әрине', 'сондықтан', 'жалпы', 
    'айталық', 'типа', 'короче', 'вообще', 'просто', 'блин'
}

EXPRESSIVE_INTERJECTIONS = {
    'ой', 'әй', 'ай', 'е', 'ә', 'м', 'уһ', 'ойбай', 'әттеген-ай', 
    'алақай', 'мәссаған', 'пах-пах', 'шүкір', 'қарашы', 'тоқта', 
    'тфу', 'тфү', 'уау', 'вау', 'қап'
}

STOP_LIST = {
    'і', 'де', 'да', 'та', 'те', 'бұл', 'сол', 'ол', 'мен', 'сен', 
    'біз', 'сіз', 'екі', 'үш', 'төрт', 'бес', 'алты', 'жеті', 'сегіз', 
    'тоғыз', 'он', 'не', 'ма', 'ме', 'па', 'пе', 'ба', 'бе', 'ғой', 
    'ғана', 'жоқ', 'бар', 'кім', 'неге', 'қай', 'осы', 'және', 'деп', 
    'екен', 'емес', 'тек', 'әр', 'әлде', 'әлі', 'өте', 'тіпті', 'қазір', 
    'әрі', 'кері', 'ерте', 'кеш', 'үшін', 'дейін', 'кейін', 'бері', 
    'қарай', 'туралы', 'сияқты', 'боп', 'болып', 'кеп', 'келіп', 'ап', 
    'алып', 'ет', 'өт', 'күн', 'жер', 'ел', 'адам', 'бала', 'қол', 
    'үй', 'ат', 'от', 'су', 'тау'
}

# %%
# 1.3 Helper functions
def clean_for_match(token: str) -> str:
    """Lower-case, remove leading/trailing punctuation, keep internal hyphens."""
    t = token.strip().lower()
    # Remove non-word characters at start/end (comma, period, exclamation, etc.)
    t = re.sub(r'^[\W_]+|[\W_]+$', '', t)
    return t

def is_repeated_pattern(token: str) -> bool:
    """True if token contains 3+ consecutive identical Kazakh letters."""
    return bool(re.search(r'([а-яёіңғүұқөәһ])\1{2,}', token, re.IGNORECASE))

def label_token(cleaned: str) -> str:
    """Assign one of the four tier labels based on hard-coded sets."""
    if is_repeated_pattern(cleaned) or cleaned in HESITATION_FILLERS:
        return "non_lexical_filler"
    if cleaned in DISCOURSE_FILLERS:
        return "discourse_filler"
    if cleaned in EXPRESSIVE_INTERJECTIONS:
        return "expressive_interjection"
    return "unclassified_short"

# %%
# 1.4 Candidate extraction loop
print("Extracting candidates...")
candidates_full = defaultdict(list)

for idx, sample in enumerate(ds):
    words_raw = sample.get('words', [])
    if isinstance(words_raw, str):
        try:
            words = json.loads(words_raw)
        except json.JSONDecodeError:
            words = []
    else:
        words = words_raw
        
    if not words:
        continue
        
    sentence_text = sample.get("text", "")
    audio_info = sample.get("audio", {})
    audio_path = audio_info.get("path", "") if isinstance(audio_info, dict) else ""
    
    for widx, word in enumerate(words):
        original_token = word.get("text", "")
        cleaned = clean_for_match(original_token)
        
        if (len(cleaned) <= 3 or
            is_repeated_pattern(cleaned) or
            cleaned in EXPRESSIVE_INTERJECTIONS or
            cleaned in DISCOURSE_FILLERS or
            cleaned in HESITATION_FILLERS):
            
            label = label_token(cleaned)
            
            occurrence = {
                "sample_id": idx,
                "word_idx": widx,
                "start": word.get("start", 0),
                "end": word.get("end", 0),
                "original_token": original_token,
                "cleaned": cleaned,
                "sentence": sentence_text,
                "audio_path": audio_path,
                "label": label
            }
            candidates_full[cleaned].append(occurrence)

print(f"Found {sum(len(v) for v in candidates_full.values())} total candidate tokens.")
print(f"Unique candidate words: {len(candidates_full)}")

with open("results/candidates_full.json", "w", encoding="utf-8") as f:
    json.dump(candidates_full, f, ensure_ascii=False, indent=2)

# %%
# 1.5 Auto-pruning of obvious function words
STOP_REMOVE = STOP_LIST - (HESITATION_FILLERS | DISCOURSE_FILLERS | EXPRESSIVE_INTERJECTIONS)

candidates_pruned = {}
auto_removed = []

for word, occurrences in candidates_full.items():
    if word in STOP_REMOVE:
        auto_removed.append(word)
    else:
        candidates_pruned[word] = occurrences

print(f"Auto-removed words: {len(auto_removed)}")
print(f"Unique candidate words after pruning: {len(candidates_pruned)}")

# %%
# 1.6 Output files
with open("results/candidates_pruned.json", "w", encoding="utf-8") as f:
    json.dump(candidates_pruned, f, ensure_ascii=False, indent=2)

with open("results/auto_removed_words.txt", "w", encoding="utf-8") as f:
    for word in sorted(auto_removed):
        f.write(f"{word}\n")

categories = {
    "non_lexical_filler": [],
    "discourse_filler": [],
    "expressive_interjection": [],
    "unclassified_short": []
}

word_counts = []

for word, occurrences in candidates_pruned.items():
    label = occurrences[0]["label"]
    categories[label].append(word)
    word_counts.append((word, label, len(occurrences)))

for cat_name, words in categories.items():
    with open(f"results/{cat_name}s.txt", "w", encoding="utf-8") as f:
        cat_words_sorted = sorted([(w, len(candidates_pruned[w])) for w in words], key=lambda x: x[1], reverse=True)
        for w, count in cat_words_sorted:
            f.write(f"{w}\n")

word_counts.sort(key=lambda x: x[2], reverse=True)
with open("results/words_for_manual_review.tsv", "w", encoding="utf-8") as f:
    f.write("word\tlabel\tcount\n")
    for word, label, count in word_counts:
        f.write(f"{word}\t{label}\t{count}\n")

print("\n--- Summary ---")
total_pruned_tokens = sum(len(v) for v in candidates_pruned.values())
print(f"Total candidate tokens (after pruning): {total_pruned_tokens}")
print(f"Unique words before pruning: {len(candidates_full)}")
print(f"Unique words after pruning: {len(candidates_pruned)}")
print("\nCounts per category (unique words):")
for cat_name, words in categories.items():
    print(f"  {cat_name}: {len(words)}")

print("\nTop 20 words by frequency:")
for word, label, count in word_counts[:20]:
    print(f"  {word} ({label}): {count}")

# %% [markdown]
# ## Part 2 - LLM Prompt Generation

# %%
llm_jsonl_path = "results/llm_prompts.jsonl"
llm_txt_path = "results/llm_prompts.txt"

unclassified_words = categories["unclassified_short"]
unclassified_words_sorted = sorted([(w, len(candidates_pruned[w])) for w in unclassified_words], key=lambda x: x[1], reverse=True)

with open(llm_jsonl_path, "w", encoding="utf-8") as f_jsonl, \
     open(llm_txt_path, "w", encoding="utf-8") as f_txt:
    
    for word, _ in unclassified_words_sorted:
        occurrences = candidates_pruned[word]
        examples = []
        seen_sentences = set()
        
        for occ in occurrences:
            sent = occ["sentence"].strip()
            if sent and sent not in seen_sentences:
                examples.append(sent)
                seen_sentences.add(sent)
            if len(examples) >= 3:
                break
                
        jsonl_obj = {"word": word, "examples": examples}
        f_jsonl.write(json.dumps(jsonl_obj, ensure_ascii=False) + "\n")
        
        f_txt.write(f"Word: {word}\nSentences:\n")
        for i, ex in enumerate(examples, 1):
            f_txt.write(f"  {i}. {ex}\n")
        f_txt.write("\n")

print(f"LLM prompts generated for {len(unclassified_words)} unclassified words.")

# %% [markdown]
# ## Part 3 - Interactive In-Notebook Review (Recommended)
# The following cells use `pandas` and `ipywidgets` to create an interactive review tool.

# %%
import pandas as pd
import ipywidgets as widgets
from IPython.display import clear_output, display, Audio
import wave
import io
import os
import json

# Load the TSV review file
df = pd.read_csv("results/words_for_manual_review.tsv", sep="\t")
print(f"Loaded {len(df)} words for review.")

# Load the candidates JSON so this cell can run independently
with open("results/candidates_pruned.json", "r", encoding="utf-8") as f:
    candidates_pruned = json.load(f)


# %%
os.makedirs("results/audio_previews", exist_ok=True)

def get_audio_snippet(sample_id, start_sec, end_sec, word="snippet"):
    """Save full sentence audio as WAV and return a download link."""
    try:
        import soundfile as sf
        import io
        from IPython.display import HTML
        
        global ds
        if 'ds' not in globals():
            from datasets import load_dataset, Audio as HfAudio
            print("Loading dataset for audio playback...")
            ds = load_dataset("govnejri/kazakh_speech_mfa_punctuation", split="train", cache_dir="/media/storage/huggingface", verification_mode="no_checks")
            if "audio" in ds.features and getattr(ds.features["audio"], "decode", True):
                ds = ds.cast_column("audio", HfAudio(decode=False))
        
        sample = ds[sample_id]
        audio_dict = sample.get("audio", {})
        
        if "bytes" not in audio_dict:
            return "No raw audio bytes found in dataset."
            
        audio_bytes = audio_dict["bytes"]
        # Decode full sentence audio
        audio_data, sr = sf.read(io.BytesIO(audio_bytes))
        
        # Save full sentence to WAV
        fname = f"results/audio_previews/{word}_s{sample_id}_full.wav"
        sf.write(fname, audio_data, sr, format='WAV', subtype='PCM_16')
        
        duration = len(audio_data) / sr
        word_start = start_sec
        word_end = end_sec
        
        return HTML(f"""
        <b>Full sentence audio</b> ({duration:.2f}s) — word '<i>{word}</i>' is at {word_start:.2f}s–{word_end:.2f}s<br>
        <audio controls>
          <source src="{fname}" type="audio/wav">
          Your browser does not support audio.
        </audio>
        <br><a href="{fname}" download>⬇ Download full sentence WAV</a>
        """)

    except Exception as e:
        return f"Error loading audio: {str(e)}"


# Dropdown to select word
word_dropdown = widgets.Dropdown(
    options=sorted(df['word'].dropna().unique()),
    description='Word:',
)

# Output area
audio_output = widgets.Output()

def on_word_change(change):
    word = change['new']
    with audio_output:
        clear_output(wait=True)
        # Find occurrences of this word from candidates_pruned
        occs = candidates_pruned.get(word, [])
        if not occs:
            print("No occurrences found.")
            return
        # Show first 3 occurrences
        for i, occ in enumerate(occs[:3]):
            print(f"--- Occurrence {i+1} ---")
            print(f"Sentence: {occ['sentence']}")
            snippet = get_audio_snippet(occ['sample_id'], occ['start'], occ['end'], word=word)
            if isinstance(snippet, str):
                print(snippet)
            else:
                display(snippet)

word_dropdown.observe(on_word_change, names='value')
print("Select a word from the dropdown to review audio snippets:")
display(word_dropdown, audio_output)

# Trigger initial display
if word_dropdown.options:
    word_dropdown.value = word_dropdown.options[0]

# %%
# Find specific word occurrences (e.g., "ааз")
target_word = "ааз"
print(f"Occurrences for '{target_word}':")
if target_word in candidates_pruned:
    occs = candidates_pruned[target_word]
    print(f"Found {len(occs)} occurrences.")
    for i, occ in enumerate(occs):
        print(f"\n--- Occurrence {i+1} ---")
        print(f"Sample ID (index): {occ['sample_id']}")
        print(f"Sentence: {occ['sentence']}")
        print(f"Audio Path: {occ['audio_path']}")
        print(f"Time: {occ['start']}s - {occ['end']}s")
        snippet = get_audio_snippet(occ['sample_id'], occ['start'], occ['end'], word=target_word)
        if isinstance(snippet, str):
            print(snippet)
        else:
            display(snippet)
        
        # Limit to first 5 to avoid spamming the notebook
        if i >= 4:
            print("\n... (showing first 5 occurrences only)")
            break
else:
    print(f"'{target_word}' not found in candidates_pruned.")
