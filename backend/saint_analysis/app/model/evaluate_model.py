import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import torch
import pickle
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score
from torch.utils.data import DataLoader
from app.dataset.saint_dataset import SAINTDataset
from app.model.saint_with_memory import SAINTModelWithMemory
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = os.getenv("DATA_DIR")
VALID_FILE = os.path.join(DATA_DIR, os.getenv("VALID_FILE"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
MODEL_PATH = os.getenv("MODEL_PATH")
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 32))

# Load dataset
with open(os.path.join(OUTPUT_DIR, "q2id.pkl"), "rb") as f:
    q2id = pickle.load(f)
with open(os.path.join(OUTPUT_DIR, "s2id.pkl"), "rb") as f:
    s2id = pickle.load(f)

valid_dataset = SAINTDataset(VALID_FILE, q2id=q2id, s2id=s2id)
valid_loader = DataLoader(valid_dataset, batch_size=BATCH_SIZE)

num_questions = len(q2id)
num_skills = len(s2id)

# Load model
model = SAINTModelWithMemory(num_questions=num_questions, num_skills=num_skills).to(DEVICE)
model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
model.eval()

# Evaluation
all_preds, all_labels = [], []

with torch.no_grad():
    for batch in valid_loader:
        q = batch['question_ids'].to(DEVICE)
        s = batch['skill_ids'].to(DEVICE)
        a = batch['answers'].to(DEVICE)
        t = batch['response_times'].to(DEVICE)
        tg = batch['time_gaps'].to(DEVICE)
        sess = batch['session_ids'].to(DEVICE)

        out = model(q, s, a, t, time_gaps=tg, session_ids=sess)
        mask = q != 0
        preds = torch.sigmoid(out[mask]).cpu().numpy()
        labels = a[mask].cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels)

auc = roc_auc_score(all_labels, all_preds)
acc = accuracy_score(all_labels, [int(p >= 0.5) for p in all_preds])

print(f"✅ Đánh giá mô hình: AUC = {auc:.4f}, ACC = {acc:.4f}")