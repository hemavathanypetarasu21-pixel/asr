"""Builds notebooks/finetune_whisper_lora.ipynb (run it on Google Colab or Kaggle with a T4 GPU)."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CELLS = [
    ("markdown", """# LingoSync: LoRA fine-tuning of Whisper-small for Malay-English and Tamil-English

Runs on a free **T4 GPU** (Colab: *Runtime > Change runtime type > T4 GPU*; Kaggle: *Accelerator > GPU T4*).

**Before running:** upload `training/outputs/lingosync_data.zip` (made by `scripts/package_for_colab.py`) to Google Drive at `MyDrive/lingosync/lingosync_data.zip`.

What this does:
1. Loads the speaker-independent **train** and **validation** splits (the **test** split stays on your laptop and is never seen here).
2. Adds **LoRA adapters** (rank 32 on the attention query/value projections, about 1-2% of the weights) to `openai/whisper-small`. The base weights stay frozen, which is what makes training fit a free GPU.
3. Trains with the Whisper language token set per clip: `<|ms|>` for Malay-English, `<|ta|>` for Tamil-English (targets are romanised Tanglish).
4. Reports validation WER per language pair, merges the adapters into the model, and saves it to Drive.

Checkpoints are saved to Drive every 500 steps; if the session disconnects, run all cells again and it resumes."""),
    ("code", """# Pinned versions known to work together. If installation conflicts with the runtime, remove the pins.
!pip -q install "transformers==4.46.3" "peft==0.13.2" "accelerate==1.1.1" jiwer soundfile"""),
    ("code", """import os
IN_COLAB = os.path.exists('/content')
if IN_COLAB:
    from google.colab import drive
    drive.mount('/content/drive')
    BASE_DIR = '/content/drive/MyDrive/lingosync'
    WORK = '/content'
else:  # Kaggle: add lingosync_data.zip as a dataset input
    BASE_DIR = '/kaggle/working/lingosync'
    WORK = '/kaggle/working'
DATA_ZIP = f'{BASE_DIR}/lingosync_data.zip' if IN_COLAB else '/kaggle/input/lingosync-data/lingosync_data.zip'
OUT_DIR = f'{BASE_DIR}/whisper-small-lingosync'
CHECKPOINTS = f'{BASE_DIR}/checkpoints'
DATA = f'{WORK}/data_root'
os.makedirs(BASE_DIR, exist_ok=True)
!unzip -q -o "$DATA_ZIP" -d "$DATA"
!nvidia-smi --query-gpu=name,memory.total --format=csv"""),
    ("code", """import math
import numpy as np
import pandas as pd
import soundfile as sf
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

BASE_MODEL = 'openai/whisper-small'
LANGUAGE = {'malay_english': 'ms', 'tamil_english': 'ta'}
processor = WhisperProcessor.from_pretrained(BASE_MODEL)

train_rows = pd.read_csv(f'{DATA}/data/splits/train/manifest.csv')
validation_rows = pd.read_csv(f'{DATA}/data/splits/validation/manifest.csv')
print(train_rows.groupby('language_pair').duration.agg(['count', 'sum']).assign(hours=lambda f: f['sum'] / 3600))


class SpeechDataset(torch.utils.data.Dataset):
    def __init__(self, rows):
        self.rows = rows.to_dict('records')

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        audio, _ = sf.read(f"{DATA}/{row['audio_path']}", dtype='float32')
        features = processor.feature_extractor(audio, sampling_rate=16000).input_features[0]
        processor.tokenizer.set_prefix_tokens(language=LANGUAGE[row['language_pair']], task='transcribe')
        labels = processor.tokenizer(str(row['training_text'])).input_ids
        return {'input_features': features, 'labels': labels}


def collate(batch):
    features = processor.feature_extractor.pad([{'input_features': item['input_features']} for item in batch], return_tensors='pt')
    labels = processor.tokenizer.pad([{'input_ids': item['labels']} for item in batch], return_tensors='pt')
    label_ids = labels['input_ids'].masked_fill(labels['attention_mask'].ne(1), -100)
    # The model adds <|startoftranscript|> itself; drop it from the labels if the tokenizer added it.
    if (label_ids[:, 0] == processor.tokenizer.convert_tokens_to_ids('<|startoftranscript|>')).all():
        label_ids = label_ids[:, 1:]
    return {'input_features': features['input_features'], 'labels': label_ids}


train_set, validation_set = SpeechDataset(train_rows), SpeechDataset(validation_rows)"""),
    ("code", """from peft import LoraConfig, get_peft_model

model = WhisperForConditionalGeneration.from_pretrained(BASE_MODEL)
model.config.forced_decoder_ids = None
model.generation_config.forced_decoder_ids = None
lora = LoraConfig(r=32, lora_alpha=64, target_modules=['q_proj', 'v_proj'], lora_dropout=0.05, bias='none')
model = get_peft_model(model, lora)
model.print_trainable_parameters()"""),
    ("code", """from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments

BATCH_SIZE = 16
EPOCHS = 2
MAX_STEPS = math.ceil(len(train_set) / BATCH_SIZE) * EPOCHS
print('training steps:', MAX_STEPS)

args = Seq2SeqTrainingArguments(
    output_dir=CHECKPOINTS,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    learning_rate=1e-3,
    warmup_steps=100,
    max_steps=MAX_STEPS,
    fp16=True,
    eval_strategy='steps',
    eval_steps=500,
    save_steps=500,
    save_total_limit=2,
    logging_steps=50,
    remove_unused_columns=False,
    label_names=['labels'],
    dataloader_num_workers=2,
    report_to='none',
)
trainer = Seq2SeqTrainer(model=model, args=args, train_dataset=train_set, eval_dataset=validation_set, data_collator=collate)
has_checkpoint = os.path.isdir(CHECKPOINTS) and any(name.startswith('checkpoint-') for name in os.listdir(CHECKPOINTS))
trainer.train(resume_from_checkpoint=has_checkpoint or None)"""),
    ("code", """# Validation WER per language pair (greedy decoding with the language token forced).
import re
import jiwer

def normalise(text):
    # \\w does not cover Tamil vowel signs, so the Tamil block is kept explicitly.
    return re.sub(r'\\s+', ' ', re.sub(r"[^\\w\\s'\\u0b80-\\u0bff]", ' ', str(text).lower())).strip()

model.eval()
results = {}
for pair, rows in validation_rows.groupby('language_pair'):
    rows = rows.sample(min(300, len(rows)), random_state=13)
    hypotheses = []
    for start in range(0, len(rows), BATCH_SIZE):
        chunk = rows.iloc[start:start + BATCH_SIZE]
        audio = [sf.read(f"{DATA}/{path}", dtype='float32')[0] for path in chunk.audio_path]
        features = processor.feature_extractor(audio, sampling_rate=16000, return_tensors='pt').input_features.to('cuda', torch.float16)
        with torch.no_grad(), torch.autocast('cuda'):
            ids = model.generate(input_features=features, language=LANGUAGE[pair], task='transcribe', max_new_tokens=225)
        hypotheses += processor.batch_decode(ids, skip_special_tokens=True)
    references = [normalise(text) for text in rows.training_text]
    hypotheses = [normalise(text) for text in hypotheses]
    results[pair] = {'clips': len(rows), 'wer': jiwer.wer(references, hypotheses), 'cer': jiwer.cer(references, hypotheses)}
    for reference, hypothesis in list(zip(references, hypotheses))[:3]:
        print(f'{pair}\\n  REF: {reference}\\n  HYP: {hypothesis}')
print(results)"""),
    ("code", """# Merge the LoRA adapters into the base weights and save a normal Whisper model for the app.
merged = model.merge_and_unload()
merged.save_pretrained(OUT_DIR, safe_serialization=True)
processor.save_pretrained(OUT_DIR)
import json
with open(f'{OUT_DIR}/validation_results.json', 'w') as handle:
    json.dump(results, handle, indent=2)
print('saved to', OUT_DIR)
# Download this folder to D:\\\\asr\\\\training\\\\outputs\\\\whisper-small-lingosync on your laptop."""),
]


def main() -> None:
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"accelerator": "GPU", "kernelspec": {"name": "python3", "display_name": "Python 3"}},
        "cells": [
            {"cell_type": kind, "metadata": {}, "source": source.splitlines(keepends=True),
             **({"outputs": [], "execution_count": None} if kind == "code" else {})}
            for kind, source in CELLS
        ],
    }
    path = ROOT / "notebooks" / "finetune_whisper_lora.ipynb"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
