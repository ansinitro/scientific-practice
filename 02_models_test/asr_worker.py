import os, sys, json, time, warnings
warnings.filterwarnings('ignore')
import torch
import librosa
from pathlib import Path

# Model name from argument
model_name = sys.argv[1] if len(sys.argv) > 1 else None
if not model_name:
    print("Usage: python asr_worker.py <model>")
    sys.exit(1)

AUDIO_SETS = {
    "shala_audio": Path("data/shala_audio"),
    "kk_audio":    Path("data/kk_audio"),
}
SUPPORTED_EXT = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}

def get_audio_files(directory):
    return sorted([f for f in directory.glob("*.*") if f.suffix.lower() in SUPPORTED_EXT])

def load_audio_and_duration(path, target_sr=16000):
    audio, sr = librosa.load(str(path), sr=target_sr, mono=True)
    duration = len(audio) / sr
    return audio, sr, duration

def evaluate(func):
    results = {}
    for ds_name, ds_path in AUDIO_SETS.items():
        ds_results = []
        for f in get_audio_files(ds_path):
            print(f"  [{ds_name}] {f.name} ...", end=" ", flush=True)
            try:
                text, elapsed, dur = func(f)
                ds_results.append({
                    "file": f.name,
                    "text": text,
                    "elapsed": elapsed,
                    "duration": dur,
                    "rtf": elapsed / dur if dur > 0 else None
                })
                print(f"RTF={elapsed/dur:.3f}")
            except Exception as e:
                print(f"ERROR: {e}")
                ds_results.append({
                    "file": f.name,
                    "text": f"[ERROR: {e}]",
                    "elapsed": 0.0,
                    "duration": 0.0,
                    "rtf": None
                })
        results[ds_name] = ds_results
    out_path = Path("results") / f"{model_name}.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved {model_name} results to {out_path}")

# ---------- Model loaders ----------
if model_name == "soyle":
    from transformers import AutoTokenizer, AutoFeatureExtractor
    from optimum.onnxruntime import ORTModelForSpeechSeq2Seq
    import onnxruntime as ort
    provider = "CUDAExecutionProvider" if "CUDAExecutionProvider" in ort.get_available_providers() else "CPUExecutionProvider"
    model = ORTModelForSpeechSeq2Seq.from_pretrained(
        "dhcppc0/soyle_onnx",
        provider=provider,
        encoder_file_name="encoder_model.onnx",
        decoder_file_name="decoder_model.onnx",
        decoder_with_past_file_name="decoder_with_past_model.onnx",
    )
    tokenizer = AutoTokenizer.from_pretrained("dhcppc0/soyle_onnx")
    extractor = AutoFeatureExtractor.from_pretrained("dhcppc0/soyle_onnx")
    device = "cuda" if provider == "CUDAExecutionProvider" else "cpu"
    model.to(device)
    def infer(f):
        audio, sr, dur = load_audio_and_duration(f)
        inputs = extractor(audio, sampling_rate=sr, return_tensors="pt").to(device)
        start = time.time()
        with torch.no_grad():
            generated_ids = model.generate(**inputs, language="<|kk|>", task="transcribe")
        elapsed = time.time() - start
        text = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return text, elapsed, dur

elif model_name == "fastconformer":
    import nemo.collections.asr as nemo_asr
    model = nemo_asr.models.EncDecHybridRNNTCTCBPEModel.from_pretrained(
        "nvidia/stt_kk_ru_fastconformer_hybrid_large"
    ).cuda().eval()
    def infer(f):
        audio, sr, dur = load_audio_and_duration(f)
        start = time.time()
        result = model.transcribe([audio], batch_size=1)
        elapsed = time.time() - start
        def extract_text(x):
            if isinstance(x, str):
                return x
            if isinstance(x, list) and len(x) > 0:
                return extract_text(x[0])
            if hasattr(x, "text"):
                return x.text
            return str(x)
        text = extract_text(result).strip()
        return text, elapsed, dur

elif model_name == "quartznet":
    import nemo.collections.asr as nemo_asr
    from huggingface_hub import hf_hub_download
    nemo_path = hf_hub_download(
        repo_id="transiteration/stt_kz_quartznet15x5",
        filename="models/stt_kz_quartznet15x5.nemo"
    )
    model = nemo_asr.models.EncDecCTCModel.restore_from(nemo_path).cuda().eval()
    def infer(f):
        audio, sr, dur = load_audio_and_duration(f)
        start = time.time()
        result = model.transcribe([audio], batch_size=1)
        elapsed = time.time() - start
        if isinstance(result, str):
            text = result
        elif isinstance(result, list) and len(result) > 0:
            first = result[0]
            text = first if isinstance(first, str) else (first.text if hasattr(first, "text") else str(first))
        else:
            text = str(result)
        return text.strip(), elapsed, dur

elif model_name == "whisper-turbo":
    from transformers import WhisperProcessor, WhisperForConditionalGeneration
    processor = WhisperProcessor.from_pretrained("abilmansplus/whisper-turbo-ksc2")
    model = WhisperForConditionalGeneration.from_pretrained(
        "abilmansplus/whisper-turbo-ksc2",
        torch_dtype=torch.float16,
        device_map="cuda"
    )
    model.eval()
    def infer(f):
        audio, sr, dur = load_audio_and_duration(f)
        input_features = processor(
            audio, sampling_rate=sr, return_tensors="pt"
        ).input_features.to(device="cuda", dtype=torch.float16)
        start = time.time()
        with torch.no_grad():
            generated_ids = model.generate(input_features)
        elapsed = time.time() - start
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        return text, elapsed, dur

else:
    print(f"Unknown model: {model_name}")
    sys.exit(1)

evaluate(infer)
