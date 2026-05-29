import csv
import json
import re
import ast
from pathlib import Path

# Paths
CWD = Path(__file__).parent
CSV_PATH = CWD / "transcriptions_combined.csv"
OUT_JSON_PATH = CWD / "results_aligned.json"

def clean_transcription(text, model):
    if not isinstance(text, str):
        return ""
    text = text.strip()
    if not text:
        return ""
    
    # Fastconformer specific tuple cleaning
    if model == "fastconformer" and (text.startswith("(['") or text.startswith("([\"")):
        try:
            parsed = ast.literal_eval(text)
            if isinstance(parsed, tuple) and len(parsed) > 0:
                first = parsed[0]
                if isinstance(first, list) and len(first) > 0:
                    text = first[0]
                elif isinstance(first, str):
                    text = first
        except Exception:
            # Fallback regex if ast fails
            match = re.search(r"^\(\['(.*?)'\]", text)
            if match:
                text = match.group(1)
    
    # Strip brackets if any are left
    if text.startswith("['") and text.endswith("']"):
        text = text[2:-2]
        
    return text.strip()

def group_words_into_segments(words, duration, words_per_segment=5):
    total_words = len(words)
    if total_words == 0:
        return []
    
    word_duration = duration / total_words
    
    segments = []
    for i in range(0, total_words, words_per_segment):
        chunk = words[i:i + words_per_segment]
        chunk_text = " ".join(chunk)
        
        start_time = i * word_duration
        end_time = min(duration, (i + len(chunk)) * word_duration)
        
        segments.append({
            "id": i // words_per_segment,
            "start": round(start_time, 2),
            "end": round(end_time, 2),
            "text": chunk_text
        })
        
    return segments

def generate_aligned_data():
    if not CSV_PATH.exists():
        print(f"CSV file not found at {CSV_PATH}")
        return

    data = []
    with open(CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset = row.get("Dataset", "").strip()
            audio_file = row.get("Audio", "").strip()
            duration = float(row.get("Duration (s)", "0") or 0)
            
            # Map video paths
            if dataset == "kk_audio":
                video_path = f"data/kk_video/{audio_file.replace('.mp3', '.mp4')}"
            else:
                video_path = f"data/shala_video/{audio_file.replace('.mp3', '.mp4')}"
                
            entry = {
                "dataset": dataset,
                "audio": audio_file,
                "video": video_path,
                "duration": duration,
                "models": {}
            }
            
            models = ["fastconformer", "quartznet", "soyle", "whisper-turbo"]
            for model in models:
                rtf_col = f"RTF_{model}"
                trans_col = f"Transcription_{model}"
                
                rtf_val = row.get(rtf_col, "")
                rtf = float(rtf_val) if rtf_val else None
                processing_time = rtf * duration if rtf is not None else None
                
                raw_text = row.get(trans_col, "")
                clean_text = clean_transcription(raw_text, model)
                
                # Tokenize and create aligned segments
                words = clean_text.split()
                segments = group_words_into_segments(words, duration)
                
                # Word-level details for interactive click-to-play
                words_with_time = []
                for idx, w in enumerate(words):
                    w_dur = duration / len(words)
                    words_with_time.append({
                        "text": w,
                        "start": round(idx * w_dur, 2),
                        "end": round((idx + 1) * w_dur, 2)
                    })
                
                entry["models"][model] = {
                    "rtf": rtf,
                    "processing_time": round(processing_time, 3) if processing_time is not None else None,
                    "text": clean_text,
                    "segments": segments,
                    "words": words_with_time
                }
                
            data.append(entry)
            
    with open(OUT_JSON_PATH, "w", encoding="utf-8") as out:
        json.dump(data, out, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved aligned subtitle segments to {OUT_JSON_PATH}")

if __name__ == "__main__":
    generate_aligned_data()
