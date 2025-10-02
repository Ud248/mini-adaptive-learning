import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from dotenv import load_dotenv
import pickle
import csv
import time
import numpy as np
import json
from sklearn.metrics import roc_auc_score, accuracy_score
from collections import defaultdict
import pandas as pd

from app.model.saint_with_memory import SAINTModelWithMemory
from app.dataset.saint_dataset import SAINTDataset

load_dotenv()
DATA_DIR = os.getenv("DATA_DIR","data/saintpp_data")
TRAIN_FILE = os.path.join(DATA_DIR, os.getenv("TRAIN_FILE"))
VALID_FILE = os.path.join(DATA_DIR, os.getenv("VALID_FILE"))
TEST_FILE = os.path.join(DATA_DIR, os.getenv("TEST_FILE"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
MODEL_PATH = os.getenv("MODEL_PATH")

EMBED_DIM = int(os.getenv("EMBED_DIM", 128))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", 32))
NUM_EPOCHS = int(os.getenv("NUM_EPOCHS", 10))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", 0.001))
DEVICE = os.getenv("DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
DROPOUT = float(os.getenv("DROPOUT", 0.1))
MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", 50))

os.makedirs(OUTPUT_DIR, exist_ok=True)

train_dataset = SAINTDataset(TRAIN_FILE)
valid_dataset = SAINTDataset(VALID_FILE, q2id=train_dataset.q2id, s2id=train_dataset.s2id)
test_dataset = SAINTDataset(TEST_FILE, q2id=train_dataset.q2id, s2id=train_dataset.s2id)
num_questions = len(train_dataset.q2id)
num_skills = len(train_dataset.s2id)

with open(os.path.join(OUTPUT_DIR, "q2id.pkl"), "wb") as f:
    pickle.dump(train_dataset.q2id, f)
with open(os.path.join(OUTPUT_DIR, "s2id.pkl"), "wb") as f:
    pickle.dump(train_dataset.s2id, f)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
valid_loader = DataLoader(valid_dataset, batch_size=BATCH_SIZE)

model = SAINTModelWithMemory(num_questions=num_questions, num_skills=num_skills).to(DEVICE)
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

best_auc = 0.0
patience = 3
no_improve_epochs = 0
log_path = os.path.join(OUTPUT_DIR, "train_log.csv")

with open(log_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["epoch", "train_loss", "val_auc", "val_acc"])

for epoch in range(NUM_EPOCHS):
    start_time = time.time()
    model.train()
    total_loss = 0
    for batch in train_loader:
        q = batch['question_ids'].to(DEVICE)
        s = batch['skill_ids'].to(DEVICE)
        a = batch['answers'].to(DEVICE)
        t = batch['response_times'].to(DEVICE)
        tg = batch['time_gaps'].to(DEVICE)
        sess = batch['session_ids'].to(DEVICE)

        out = model(q, s, a, t, time_gaps=tg, session_ids=sess)
        mask = q != 0
        preds = out[mask]
        labels = a[mask].float()

        loss = criterion(preds, labels)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    avg_loss = total_loss / len(train_loader)

    model.eval()
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
    duration = time.time() - start_time

    print(f"Epoch {epoch+1}/{NUM_EPOCHS} | Time: {duration:.2f}s | Loss: {avg_loss:.4f} | Val AUC: {auc:.4f} | Acc: {acc:.4f}")

    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([epoch+1, avg_loss, auc, acc])

    if auc > best_auc:
        best_auc = auc
        no_improve_epochs = 0
        best_model_path = os.path.join(OUTPUT_DIR, f"saint_epoch{epoch+1}_auc{auc:.4f}.pt")
        torch.save(model.state_dict(), best_model_path)
        print(f"✅ Đã lưu mô hình tốt nhất tại: {best_model_path}")
    else:
        no_improve_epochs += 1
        if no_improve_epochs >= patience:
            print("⏹️ Early stopping do không cải thiện AUC")
            break
