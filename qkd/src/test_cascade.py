import unittest

from unittest.mock import MagicMock

import cascade

class FakeSocket():
    def send():
       pass

    def recv():
       pass

class TestCascade(unittest.TestCase):
    def test_quantum_bit_error_rate(self):
        local = [0, 1, 1, 0, 0]
        remote = [1, 1, 0, 1, 0]
        qber = cascade.quantum_bit_error_rate(local, remote)
        self.assertEqual(qber, 0.6)

    def test_block_parity_from_indices(self):
        key = [0, 1, 1, 1, 0]

        index_cases = [
            [2, 0, 4],
            [0, 1, 3],
        ]

        expected_parities = [1, 0]

        for i in range(len(index_cases)):
            indices = index_cases[i]
            expected_parity = expected_parities[i]
            parity = cascade.get_block_parity_from_indices(key, indices)
            self.assertEqual(parity, expected_parity)

    def test_listen_and_respond_block_parity(self):
        key = [0, 1, 0, 1, 1, 0]

        socket = FakeSocket()

        socket.recv = MagicMock()
        socket.recv.side_effect = ["3,1,5", "1,3,4", "STOP"]

        socket.send = MagicMock()

        cascade.listen_and_respond_block_parity(key, socket)
        socket.recv.assert_called()
        socket.send.assert_any_call("0")
        socket.send.assert_any_call("1")

    def test_binary_algorithm(self):
        incorrect_key = [0, 1, 0, 0, 0, 1]
        indices = [*range(len(incorrect_key))]

        left_block = incorrect_key[:3]
        right_block = incorrect_key[3:]

        left_block_indices = indices[:3]
        right_block_indices = indices[3:]

        ask_parity_fn = MagicMock()
        ask_parity_fn.side_effect = [1]

        # Demonstrate correcting a bit.
        result = cascade.binary_algorithm(
            left_block,
            left_block_indices,
            ask_parity_fn,
        )
        self.assertEqual(result.tolist(), [0, 1, 1])

if __name__ == "__main__":
    unittest.main()
