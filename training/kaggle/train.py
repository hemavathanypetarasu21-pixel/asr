"""Kaggle GPU job: LoRA fine-tuning of Whisper-small on the LingoSync dataset.

Pushed with `kaggle kernels push -p training/kaggle`; the private dataset
hemavathanypetarasu/lingosync-data supplies lingosync_data.zip and finetune_lora.py.
The fine-tuned model is written to /kaggle/working/whisper-small-lingosync.
"""

import glob
import os
import shutil
import socket
import subprocess
import sys
import zipfile

INPUT = "/kaggle/input"
WORK = "/kaggle/working"
DATA_ROOT = f"{WORK}/data_root"
OUTPUT = f"{WORK}/whisper-small-lingosync"

subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv"], check=False)
try:
    socket.create_connection(("pypi.org", 443), timeout=10).close()
except OSError:
    sys.exit("No internet access: Kaggle only enables internet (and GPUs) after phone verification "
             "(kaggle.com > Settings > Phone verification).")

# Same versions as tested locally.
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "transformers==4.46.3", "peft==0.13.2", "accelerate==1.1.1", "jiwer"], check=True)

# Kaggle may have unpacked the zip on upload; handle both cases.
archives = glob.glob(f"{INPUT}/**/lingosync_data.zip", recursive=True)
if archives:
    print("unzipping", archives[0], flush=True)
    zipfile.ZipFile(archives[0]).extractall(DATA_ROOT)
    data_root = DATA_ROOT
else:
    manifest = glob.glob(f"{INPUT}/**/data/splits/train/manifest.csv", recursive=True)[0]
    data_root = manifest.split("/data/splits/")[0]
print("data root:", data_root, flush=True)

script = glob.glob(f"{INPUT}/**/finetune_lora.py", recursive=True)[0]
subprocess.run(
    [sys.executable, script, "--gpu", "--base", "openai/whisper-small", "--data-root", data_root, "--output", OUTPUT,
     "--max-steps", "1750", "--batch-size", "16", "--save-steps", "250", "--validation-clips", "300"],
    check=True,
)

# Keep only the model in the job output (smaller download).
shutil.rmtree(DATA_ROOT, ignore_errors=True)
shutil.rmtree(f"{OUTPUT}-checkpoints", ignore_errors=True)
print("done:", os.listdir(OUTPUT), flush=True)
