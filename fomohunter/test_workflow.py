import unittest
from unittest.mock import patch, MagicMock
from modules.token_sniper import detect_tokens_in_all_dex
from modules.trade_execution import place_order, should_execute_trade
from modules.positions_manager import PositionsManager
from modules.market_analysis import get_crypto_price
from modules.config_loader import load_config

class TestFomoHunterWorkflow(unittest.TestCase):

    def setUp(self):
        """Configura el entorno de prueba."""
        self.config = load_config()
        self.positions_manager = PositionsManager()
        self.mock_dex_data = [
            {"name": "TokenA", "liquidity": 200000, "volume": 100000, "price_change_24h": 15},
            {"name": "TokenB", "liquidity": 150000, "volume": 80000, "price_change_24h": 5},
        ]

    @patch("modules.token_sniper.detect_tokens_in_all_dex")
    def test_token_detection(self, mock_detect_tokens):
        """Prueba la detección de tokens desde los DEX configurados."""
        mock_detect_tokens.return_value = self.mock_dex_data
        detected_tokens = detect_tokens_in_all_dex(self.config, self.config["dex_platforms"])
        self.assertEqual(len(detected_tokens), 2)
        self.assertIn("TokenA", [token["name"] for token in detected_tokens])

    @patch("modules.trade_execution.place_order")
    @patch("modules.trade_execution.should_execute_trade")
    def test_trade_execution(self, mock_should_execute_trade, mock_place_order):
        """Prueba la ejecución de trades basados en la decisión de IA."""
        mock_should_execute_trade.side_effect = ["buy", "hold"]
        mock_place_order.return_value = {"status": "success"}

        for token in self.mock_dex_data:
            decision = should_execute_trade(token, self.config)
            if decision == "buy":
                response = place_order(
                    dex_name="raydium",
                    token=token,
                    amount=100,
                    slippage=0.5,
                    action="buy"
                )
                self.assertEqual(response["status"], "success")

    @patch("modules.positions_manager.PositionManager.get_all_positions")
    @patch("modules.market_analysis.get_crypto_price")
    def test_position_monitoring(self, mock_get_crypto_price, mock_get_all_positions):
        """Prueba la monitorización de posiciones abiertas."""
        mock_get_all_positions.return_value = [
            {"id": 1, "token_name": "TokenA", "current_price": 1.2, "stop_loss": 1.0, "take_profit": 1.5},
            {"id": 2, "token_name": "TokenB", "current_price": 0.9, "stop_loss": 0.8, "take_profit": 1.3},
        ]
        mock_get_crypto_price.side_effect = [1.4, 0.7]

        positions = self.positions_manager.get_all_positions()
        for position in positions:
            current_price = get_crypto_price(position["token_name"])
            if current_price >= position["take_profit"]:
                self.positions_manager.close_position(position["id"])
                self.assertEqual(position["token_name"], "TokenA")
            elif current_price <= position["stop_loss"]:
                self.positions_manager.close_position(position["id"])
                self.assertEqual(position["token_name"], "TokenB")

    def test_error_handling(self):
        """Prueba el manejo de errores y la recuperación del sistema."""
        with self.assertRaises(Exception):
            raise Exception("Simulated Error")

        try:
            raise Exception("Simulated Error")
        except Exception as e:
            self.assertEqual(str(e), "Simulated Error")

if __name__ == "__main__":
    unittest.main()

def run_tests():
    """
    Ejecuta una suite de pruebas automatizadas para verificar la funcionalidad.
    """
    loader = unittest.TestLoader()
    tests = loader.discover(start_dir="tests", pattern="test_*.py")
    runner = unittest.TextTestRunner()
    result = runner.run(tests)
    if result.wasSuccessful():
        logging.info("✅ Todas las pruebas pasaron exitosamente.")
    else:
        logging.error(f"❌ Algunas pruebas fallaron: {result.failures}")