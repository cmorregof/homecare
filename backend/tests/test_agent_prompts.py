import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agents.doctor_agent import PROMPT_PATH as DOCTOR_PROMPT_PATH


NURSE_PROMPT_PATH = DOCTOR_PROMPT_PATH.parent / "nurse_system.txt"


class AgentPromptsTest(unittest.TestCase):
    def test_nurse_prompt_prohibits_diagnosis(self):
        prompt = NURSE_PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn("Nunca diagnostiques ni prescribas", prompt)

    def test_doctor_prompt_prohibits_prescription(self):
        prompt = DOCTOR_PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn("Nunca prescribas medicamentos", prompt)
        self.assertIn("médico tratante humano", prompt)

    def test_prompts_mandate_spanish(self):
        nurse = NURSE_PROMPT_PATH.read_text(encoding="utf-8")
        doctor = DOCTOR_PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn("responde en español", nurse)
        self.assertIn("Responde siempre en español", doctor)


if __name__ == "__main__":
    unittest.main()
