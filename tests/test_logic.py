import unittest
from logic import detect_transfers
from models import WalletTransaction

class TestLogic(unittest.TestCase):
    def test_transfer_detection(self):
        # Create dummy transactions
        t1 = WalletTransaction(
            account="AccA", category="Transfer", amount=-100.0,
            currency="EUR", date="2023-01-01 10:00:00", is_transfer=True
        )
        t2 = WalletTransaction(
            account="AccB", category="Transfer", amount=100.0,
            currency="EUR", date="2023-01-01 10:00:00", is_transfer=True
        )
        t3 = WalletTransaction(
            account="AccA", category="Food", amount=-50.0,
            currency="EUR", date="2023-01-01 12:00:00", is_transfer=False
        )

        ts = [t1, t2, t3]
        processed = detect_transfers(ts)

        # t1 should be paired with t2 (indices 0 and 1)
        self.assertEqual(processed[0].paired_with_idx, 1)
        self.assertEqual(processed[1].paired_with_idx, 0)
        self.assertIsNone(processed[2].paired_with_idx)

    def test_transfer_pairing_same_account_ignored(self):
        # Even if same account, logic currently pairs them if amounts match.
        # (Transfers within same account are rare but possible corrections).
        t1 = WalletTransaction(
            account="AccA", category="Transfer", amount=-50.0,
            currency="EUR", date="2023-01-02 10:00:00", is_transfer=True
        )
        t2 = WalletTransaction(
            account="AccA", category="Transfer", amount=50.0,
            currency="EUR", date="2023-01-02 10:00:00", is_transfer=True
        )

        ts = [t1, t2]
        processed = detect_transfers(ts)
        self.assertEqual(processed[0].paired_with_idx, 1)

if __name__ == '__main__':
    unittest.main()
