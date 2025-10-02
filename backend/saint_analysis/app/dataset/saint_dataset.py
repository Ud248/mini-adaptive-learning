import torch
from torch.utils.data import Dataset
import pandas as pd
import os
from dotenv import load_dotenv
import numpy as np
from datetime import datetime

load_dotenv()

MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", 50))

class SAINTDataset(Dataset):
    def __init__(self, file_path, q2id=None, s2id=None):
        self.data = pd.read_csv(file_path, sep='\t')
        self.data["timestamp"] = pd.to_datetime(self.data["timestamp"], errors="coerce")
        self.data = self.data.sort_values(by=["student_id", "timestamp"])

        if q2id is not None:
            self.q2id = q2id
        else:
            self.q2id = self._build_id_dict(self.data['question_id'])

        if s2id is not None:
            self.s2id = s2id
        else:
            self.s2id = self._build_id_dict(self.data['skill_id'])

        self.data['log_time'] = self.data['response_time'].apply(lambda x: np.log1p(x))
        self.samples = self._group_by_student()

    def _build_id_dict(self, series):
        items = series.unique().tolist()
        return {item: idx + 1 for idx, item in enumerate(items)}

    def _group_by_student(self):
        grouped = self.data.groupby('student_id')
        samples = []
        for _, group in grouped:
            group = group.sort_values("timestamp")
            questions = group['question_id'].tolist()
            skills = group['skill_id'].tolist()
            answers = group['correct'].tolist()
            times = group['log_time'].tolist()

            # timestamp for time gap
            timestamps = group['timestamp'].tolist()
            time_gaps = [0]
            for i in range(1, len(timestamps)):
                delta = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600.0  # hours
                bin_gap = min(int(delta // 24), 9)  # bin by day (max 9)
                time_gaps.append(bin_gap)

            # session index (every 1 day = new session)
            base_day = timestamps[0].date() if timestamps else datetime.today().date()
            session_ids = [(t.date() - base_day).days for t in timestamps]

            samples.append((questions, skills, answers, times, time_gaps, session_ids))
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        q_seq, s_seq, a_seq, t_seq, tg_seq, sess_seq = self.samples[idx]
        q_ids = [self.q2id.get(q, 0) for q in q_seq]
        s_ids = [self.s2id.get(s, 0) for s in s_seq]
        t_vals = t_seq
        tg_vals = tg_seq
        sess_ids = sess_seq

        if len(q_ids) > MAX_SEQ_LEN:
            q_ids = q_ids[-MAX_SEQ_LEN:]
            s_ids = s_ids[-MAX_SEQ_LEN:]
            a_seq = a_seq[-MAX_SEQ_LEN:]
            t_vals = t_vals[-MAX_SEQ_LEN:]
            tg_vals = tg_vals[-MAX_SEQ_LEN:]
            sess_ids = sess_ids[-MAX_SEQ_LEN:]
        else:
            pad_len = MAX_SEQ_LEN - len(q_ids)
            q_ids = [0] * pad_len + q_ids
            s_ids = [0] * pad_len + s_ids
            a_seq = [0] * pad_len + a_seq
            t_vals = [0.0] * pad_len + t_vals
            tg_vals = [0] * pad_len + tg_vals
            sess_ids = [0] * pad_len + sess_ids

        return {
            'question_ids': torch.tensor(q_ids, dtype=torch.long),
            'skill_ids': torch.tensor(s_ids, dtype=torch.long),
            'answers': torch.tensor(a_seq, dtype=torch.long),
            'response_times': torch.tensor(t_vals, dtype=torch.float),
            'time_gaps': torch.tensor(tg_vals, dtype=torch.long),
            'session_ids': torch.tensor(sess_ids, dtype=torch.long)
        }