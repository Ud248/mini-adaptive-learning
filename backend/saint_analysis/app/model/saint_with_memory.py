import torch
import torch.nn as nn
import os
from dotenv import load_dotenv

# Load cấu hình từ .env
load_dotenv()
EMBED_DIM = int(os.getenv("EMBED_DIM", 128))
NUM_HEADS = int(os.getenv("NUM_HEADS", 4))
NUM_LAYERS = int(os.getenv("NUM_LAYERS", 2))
DROPOUT = float(os.getenv("DROPOUT", 0.1))
MAX_SEQ_LEN = int(os.getenv("MAX_SEQ_LEN", 50))

class SAINTModelWithMemory(nn.Module):
    def __init__(self, num_questions, num_skills, max_sessions=100, max_timegap=10):
        super().__init__()
        self.question_embed = nn.Embedding(num_questions + 1, EMBED_DIM)
        self.answer_embed = nn.Embedding(2, EMBED_DIM)
        self.skill_embed = nn.Embedding(num_skills + 1, EMBED_DIM)
        self.position_embed = nn.Embedding(MAX_SEQ_LEN, EMBED_DIM)
        self.time_proj = nn.Linear(1, EMBED_DIM)

        # New embeddings
        self.session_embed = nn.Embedding(max_sessions, EMBED_DIM)
        self.timegap_embed = nn.Embedding(max_timegap + 1, EMBED_DIM)

        # Optional initial memory state
        self.initial_memory = nn.Parameter(torch.randn(EMBED_DIM))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=EMBED_DIM,
            nhead=NUM_HEADS,
            dropout=DROPOUT,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=NUM_LAYERS)
        self.prediction = nn.Linear(EMBED_DIM, 1)

    def forward(self, question_ids, skill_ids, answers, response_times, session_ids=None, time_gaps=None):
        # Input shape: [batch, seq]
        q_embed = self.question_embed(question_ids)
        a_embed = self.answer_embed(answers)
        s_embed = self.skill_embed(skill_ids)

        pos_ids = torch.arange(question_ids.size(1), device=question_ids.device).unsqueeze(0)
        pos_embed = self.position_embed(pos_ids)
        t_embed = self.time_proj(response_times.unsqueeze(-1))

        sess_embed = self.session_embed(session_ids) if session_ids is not None else 0
        tg_embed = self.timegap_embed(time_gaps) if time_gaps is not None else 0

        x = q_embed + a_embed + s_embed + pos_embed + t_embed + sess_embed + tg_embed

        # Inject memory at first position
        x[:, 0, :] += self.initial_memory

        x = self.transformer(x)
        out = self.prediction(x)
        return out.squeeze(-1)
