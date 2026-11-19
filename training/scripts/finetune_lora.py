"""LoRA fine-tuning of Whisper on this computer's CPU (same method as notebooks/finetune_whisper_lora.ipynb).

Trains on data/splits/train, checks loss on a fixed sample of data/splits/validation, and saves a
merged Hugging Face model that the app and scripts/evaluate.py can load. Checkpoints are written
every --save-steps, so an interrupted run continues where it stopped when started again.
While it runs, Windows is asked not to sleep (the setting is released when the script ends).

Usage (from training/):
    python scripts/finetune_lora.py --base openai/whisper-base --benchmark 3     # time a few steps
    python scripts/finetune_lora.py --base openai/whisper-base --max-steps 1500
"""

import argparse
import ctypes
import json
import math
import sys
import time
from pathlib import Path

import pandas as pd
import soundfile as sf
import torch

ROOT = Path(__file__).resolve().parents[1]
LANGUAGE = {"malay_english": "ms", "tamil_english": "ta"}


def keep_awake() -> None:
    if sys.platform == "win32":
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)


class SpeechDataset(torch.utils.data.Dataset):
    def __init__(self, rows: pd.DataFrame, processor):
        self.rows = rows.to_dict("records")
        self.processor = processor

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        audio, _ = sf.read(ROOT / row["audio_path"], dtype="float32")
        features = self.processor.feature_extractor(audio, sampling_rate=16000).input_features[0]
        self.processor.tokenizer.set_prefix_tokens(language=LANGUAGE[row["language_pair"]], task="transcribe")
        labels = self.processor.tokenizer(str(row["training_text"])).input_ids
        return {"input_features": features, "labels": labels}


class Collator:
    def __init__(self, processor):
        self.processor = processor
        self.start = processor.tokenizer.convert_tokens_to_ids("<|startoftranscript|>")

    def __call__(self, batch):
        features = self.processor.feature_extractor.pad([{"input_features": item["input_features"]} for item in batch], return_tensors="pt")
        labels = self.processor.tokenizer.pad([{"input_ids": item["labels"]} for item in batch], return_tensors="pt")
        label_ids = labels["input_ids"].masked_fill(labels["attention_mask"].ne(1), -100)
        # The model prepends <|startoftranscript|> itself.
        if (label_ids[:, 0] == self.start).all():
            label_ids = label_ids[:, 1:]
        return {"input_features": features["input_features"], "labels": label_ids}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="openai/whisper-base")
    parser.add_argument("--output", default="outputs/whisper-base-lingosync")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--max-steps", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=1e-3)
    parser.add_argument("--save-steps", type=int, default=100)
    parser.add_argument("--validation-clips", type=int, default=200, help="fixed validation sample for loss checks")
    parser.add_argument("--benchmark", type=int, default=0, help="only time this many training steps, then exit")
    args = parser.parse_args()

    import truststore

    truststore.inject_into_ssl()
    from peft import LoraConfig, get_peft_model
    from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments, WhisperForConditionalGeneration, WhisperProcessor

    keep_awake()
    torch.manual_seed(13)
    processor = WhisperProcessor.from_pretrained(args.base)
    train_rows = pd.read_csv(ROOT / "data/splits/train/manifest.csv").sample(frac=1, random_state=13)
    validation_rows = (pd.read_csv(ROOT / "data/splits/validation/manifest.csv")
                       .groupby("language_pair", group_keys=False)
                       .apply(lambda frame: frame.sample(min(args.validation_clips // 2, len(frame)), random_state=13)))
    train_set, validation_set = SpeechDataset(train_rows, processor), SpeechDataset(validation_rows, processor)

    model = WhisperForConditionalGeneration.from_pretrained(args.base)
    model.config.forced_decoder_ids = None
    model.generation_config.forced_decoder_ids = None
    model = get_peft_model(model, LoraConfig(r=32, lora_alpha=64, target_modules=["q_proj", "v_proj"], lora_dropout=0.05, bias="none"))
    model.print_trainable_parameters()

    output = ROOT / args.output
    checkpoints = output.with_name(output.name + "-checkpoints")
    max_steps = args.benchmark or args.max_steps
    epochs = max_steps * args.batch_size / len(train_set)
    print(f"train clips {len(train_set)}, validation clips {len(validation_set)}, steps {max_steps} (~{epochs:.2f} epochs)", flush=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=str(checkpoints),
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        warmup_steps=min(100, max_steps // 10),
        max_steps=max_steps,
        use_cpu=True,
        eval_strategy="no" if args.benchmark else "steps",
        eval_steps=args.save_steps * 3,
        save_steps=args.save_steps,
        save_total_limit=2,
        logging_steps=1 if args.benchmark else 10,
        remove_unused_columns=False,
        label_names=["labels"],
        dataloader_num_workers=0,
        report_to="none",
        save_strategy="no" if args.benchmark else "steps",
    )
    trainer = Seq2SeqTrainer(model=model, args=training_args, train_dataset=train_set, eval_dataset=validation_set, data_collator=Collator(processor))

    started = time.time()
    if args.benchmark:
        trainer.train()
        per_step = (time.time() - started) / args.benchmark
        print(f"BENCHMARK: {per_step:.1f} s per step of {args.batch_size} clips "
              f"-> 1000 steps ~ {per_step * 1000 / 3600:.1f} h, one epoch ({math.ceil(len(train_set) / args.batch_size)} steps) "
              f"~ {per_step * len(train_set) / args.batch_size / 3600:.1f} h", flush=True)
        return

    resume = checkpoints.is_dir() and any(path.name.startswith("checkpoint-") for path in checkpoints.iterdir())
    trainer.train(resume_from_checkpoint=resume or None)
    final_loss = trainer.evaluate()

    merged = model.merge_and_unload()
    merged.save_pretrained(output, safe_serialization=True)
    processor.save_pretrained(output)
    info = {
        "base_model": args.base,
        "method": "LoRA r=32 alpha=64 on q_proj/v_proj (encoder and decoder), merged after training",
        "train_clips": len(train_set),
        "steps": max_steps,
        "batch_size": args.batch_size,
        "epochs": round(epochs, 2),
        "learning_rate": args.learning_rate,
        "final_validation_loss": final_loss.get("eval_loss"),
        "training_hours": round((time.time() - started) / 3600, 2),
        "train_log": trainer.state.log_history,
    }
    (output / "training_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(f"saved fine-tuned model to {output}", flush=True)


if __name__ == "__main__":
    main()
