import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "alfa_advisor.py"


class SourceStructureTests(unittest.TestCase):
    def test_source_exists_and_compiles(self):
        source_text = SOURCE.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(SOURCE))
        self.assertGreater(len(source_text), 1000)
        self.assertIsInstance(tree, ast.Module)

    def test_expected_components_are_present(self):
        source_text = SOURCE.read_text(encoding="utf-8")
        expected_symbols = (
            "CostEngine",
            "MLMetricsStore",
            "IntelligentAdvisor",
            "SafetyVault",
            "ReinforcementLearner",
            "LSTMPredictor",
            "BrokerMT5Real",
            "Backtester",
            "AlfaDivinaSuprema",
        )
        for symbol in expected_symbols:
            with self.subTest(symbol=symbol):
                self.assertIn(f"class {symbol}", source_text)

    def test_credentials_are_loaded_from_environment(self):
        source_text = SOURCE.read_text(encoding="utf-8")
        self.assertIn('os.getenv("MT5_LOGIN")', source_text)
        self.assertIn('os.getenv("MT5_SENHA")', source_text)
        self.assertIn('os.getenv("MT5_SERVIDOR")', source_text)
        self.assertNotIn("password = \"", source_text.lower())


if __name__ == "__main__":
    unittest.main()
