# LingoSync training: data, evaluation and fine-tuning

Improves LingoSync's speech recognition for Malaysian **Malay-English** and **Tamil-English** code-mixed speech using real, licensed speech datasets. Nothing in this folder changes how the app runs until a fine-tuned model is added to `backend/.env` (see the last section).

## Folder layout

```
datasets.json                         every dataset considered: source URL, licence, size, why used or excluded
vocabulary/malaysian_code_mixed_vocabulary.json   Malay / English / Tamil colloquial and academic terms
scripts/prepare_data.py               raw corpora -> 16 kHz mono WAV clips + manifest.csv
scripts/split_data.py                 speaker-independent 70 / 15 / 15 train / validation / test split
scripts/evaluate.py                   WER / CER per language pair, original vs fine-tuned model
scripts/package_for_colab.py          zips train + validation (FLAC) for upload to Google Drive
scripts/build_notebook.py             regenerates notebooks/finetune_whisper_lora.ipynb
notebooks/finetune_whisper_lora.ipynb LoRA fine-tuning of Whisper-small on a free Colab / Kaggle T4 GPU
data/      (not in git) raw downloads, prepared clips, splits
outputs/   (not in git) evaluation results, Colab zip, fine-tuned model
```

## Manifest columns

| Column | Meaning |
|---|---|
| `audio_path` | 16 kHz mono 16-bit WAV, 1-30 s |
| `transcript` | original transcript exactly as published (Tamil in Tamil script) |
| `training_text` | text the model learns: Malay-English unchanged; Tamil romanised Tanglish-style (`backend/src/services/tamil_romanisation.py`) |
| `transcript_normalised` | lower-case, no punctuation, for scoring |
| `language_pair` | `malay_english` or `tamil_english` |
| `source`, `licence` | dataset id from `datasets.json` and its licence |
| `speaker_id` | speaker (Emilia: episode + diarised speaker) |
| `duration` | seconds |
| `is_code_mixed` | Malay-English only: heuristic flag (at least one clearly-English and one clearly-Malay word by `wordfreq` frequency). Not a human label |
| `original_id` | file id in the source dataset |

Dropped automatically: undecodable files, clips under 1 s or over 30 s, silent clips and exact audio duplicates.

## Steps

```bash
cd training
pip install -r requirements.txt

# 1. Prepare (raw downloads must be in data/raw/; SLR127 must be extracted to data/raw/slr127/extracted)
python scripts/prepare_data.py emilia --max-hours 30
python scripts/prepare_data.py slr65  --max-hours 12
python scripts/prepare_data.py slr127 --max-hours 18

# 2. Split 70 / 15 / 15, speaker-independent
python scripts/split_data.py

# 3. Baseline: the app's current model, run exactly as the app runs it
python scripts/evaluate.py --model tiny  --limit 150
python scripts/evaluate.py --model medium --limit 150   # slow on CPU

# 4. Fine-tune (Google Colab / Kaggle)
python scripts/package_for_colab.py    # -> outputs/lingosync_data.zip, upload to MyDrive/lingosync/
#    open notebooks/finetune_whisper_lora.ipynb in Colab, Runtime > T4 GPU, Run all
#    download MyDrive/lingosync/whisper-small-lingosync to training/outputs/whisper-small-lingosync

# 5. Evaluate the fine-tuned model on the same test clips
python scripts/evaluate.py --hf-model outputs/whisper-small-lingosync --limit 150
```

Results land in `outputs/eval/<model>/results.json` (overall, per language pair, per source) and `predictions.csv` (every reference and hypothesis, for error analysis).

## Using the fine-tuned model in the app

In `backend/.env`:

```
RECOGNITION_MODELS=[{"id":"tiny","label":"Whisper tiny (fast)"},{"id":"medium","label":"Whisper medium (accurate)"},{"id":"lingosync-small","label":"LingoSync fine-tuned (Whisper small)"}]
FINETUNED_MODEL_DIRS={"lingosync-small": "D:/asr/training/outputs/whisper-small-lingosync"}
```

Restart the backend. The model then appears in the recognition model dropdown. Fine-tuned models are run with the Whisper language token forced (`ms` for Malay-English, `ta` for Tamil-English, from the detected or declared language), because that is how they were trained.

## Limitations (state these in the FYP report)

- **No public Tamil-English code-mixed speech corpus could be verified.** Tamil training data is monolingual read speech (SLR65, SLR127) with romanised targets. The model learns Tamil acoustics and romanised spelling from it, but not natural Tamil-English switching.
- **Romanised Tamil comes from written Tamil.** Read-speech transcripts are formal written Tamil, so romanised targets look like `naan pogiren` rather than spoken `naan poren`.
- **Emilia transcripts may be machine-generated** (the publisher does not say how they were made). Emilia is fine for training, but its test portion is not a human-verified benchmark. Report the SLR test results and your own recordings as the main human-labelled benchmark.
- **Romanised Tamil has no single correct spelling** (`innikku` / `inniku`). `loose_wer` collapses doubled letters and `th/dh/zh` variants to reduce this effect; report both.
- **Recommended:** record 30-60 minutes per language pair of real code-mixed speech with consenting speakers, transcribe it by hand (romanised Tamil), and use it as the final test set. The app already stores recordings with their declared language.
