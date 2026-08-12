"""Tests del intake ampliado según el Protocolo de medición domiciliaria v1.0.

Cubre las tres variables añadidas (frecuencia respiratoria, temperatura, peso):
parser de texto libre, construcción del mensaje crudo y rangos de validación.
"""

import unittest

from agents.nurse_agent import parse_vital_signs_message, validate_vital_signs
from bot.handlers import build_raw_message_from_draft


class ProtocolVitalsTest(unittest.TestCase):
    def test_parser_extracts_new_protocol_fields(self):
        parsed = parse_vital_signs_message(
            "Presión 130/82, respiraciones por minuto 18, pulso 78, saturación 97, "
            "temperatura 36,8, peso 68.5, glucosa 115, dolor 1, mareo 0, "
            "dificultad para respirar 0"
        )
        self.assertEqual(parsed.get("respiratory_rate"), 18)
        self.assertEqual(parsed.get("temperature"), 36.8)
        self.assertEqual(parsed.get("weight_kg"), 68.5)
        self.assertEqual(parsed.get("heart_rate"), 78)
        self.assertEqual(parsed.get("dyspnea_score"), 0)

    def test_respiratory_rate_does_not_collide_with_dyspnea(self):
        parsed = parse_vital_signs_message("frecuencia respiratoria 22 y ahogo 3")
        self.assertEqual(parsed.get("respiratory_rate"), 22)
        self.assertEqual(parsed.get("dyspnea_score"), 3)
        parsed = parse_vital_signs_message("mi respiración 16, pulso 80")
        self.assertEqual(parsed.get("respiratory_rate"), 16)
        self.assertNotIn("dyspnea_score", parsed)

    def test_raw_message_includes_new_fields(self):
        raw = build_raw_message_from_draft(
            {
                "systolic_bp": 130,
                "diastolic_bp": 82,
                "respiratory_rate": 18,
                "heart_rate": 78,
                "oxygen_saturation": 97,
                "temperature": 36.8,
                "weight_kg": 68.5,
            }
        )
        self.assertIn("respiraciones por minuto 18", raw)
        self.assertIn("temperatura 36.8", raw)
        self.assertIn("peso 68.5", raw)

    def test_validation_ranges_for_new_fields(self):
        base = {"systolic_bp": 120, "diastolic_bp": 80, "heart_rate": 70}
        self.assertEqual(validate_vital_signs({**base, "respiratory_rate": 18, "weight_kg": 70}), [])
        self.assertTrue(validate_vital_signs({**base, "respiratory_rate": 55}))
        self.assertTrue(validate_vital_signs({**base, "weight_kg": 10}))


if __name__ == "__main__":
    unittest.main()
