import os
import pickle
from dotenv import load_dotenv
from app.model.saint_with_memory import SAINTModelWithMemory
from app.dataset.saint_dataset import SAINTDataset
import torch

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR")
TEST_FILE = os.path.join(DATA_DIR, os.getenv("TEST_FILE"))
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
MODEL_PATH = os.getenv("MODEL_PATH")
DEVICE = os.getenv("DEVICE", "cpu")

class Singleton:
    _model = None
    _dataset = None
    _q2id = None
    _s2id = None

    @classmethod
    def load_q2id_s2id(cls):
        if cls._q2id is None or cls._s2id is None:
            with open(os.path.join(OUTPUT_DIR, "q2id.pkl"), "rb") as f:
                cls._q2id = pickle.load(f)
            with open(os.path.join(OUTPUT_DIR, "s2id.pkl"), "rb") as f:
                cls._s2id = pickle.load(f)
        return cls._q2id, cls._s2id

    @classmethod
    def get_model(cls) -> SAINTModelWithMemory:
        if cls._model is None:
            q2id, s2id = cls.load_q2id_s2id()
            cls._model = SAINTModelWithMemory(num_questions=len(q2id), num_skills=len(s2id)).to(DEVICE)
            cls._model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
            cls._model.eval()
        return cls._model

    @classmethod
    def get_dataset(cls) -> SAINTDataset:
        if cls._dataset is None:
            q2id, s2id = cls.load_q2id_s2id()
            cls._dataset = SAINTDataset(TEST_FILE, q2id=q2id, s2id=s2id)
        return cls._dataset

    @classmethod
    def get_q2id(cls):
        if cls._q2id is None:
            cls.load_q2id_s2id()
        return cls._q2id

    @classmethod
    def get_s2id(cls):
        if cls._s2id is None:
            cls.load_q2id_s2id()
        return cls._s2id


    @classmethod
    def set_q2id(cls, mapping):
        cls._q2id = mapping


    @classmethod
    def set_s2id(cls, mapping):
        cls._s2id = mapping
