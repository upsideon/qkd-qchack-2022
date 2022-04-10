import math
import random
import unittest

from unittest.mock import MagicMock

from netqasm.sdk.external import Socket

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

    def test_get_block_size(self):
        qber = 0.2
        initial_block_size = math.ceil(0.73 / qber)
        expected_block_sizes = [
            initial_block_size,
            2 * initial_block_size,
            4 * initial_block_size, 
            8 * initial_block_size,
        ]

        for i in range(len(expected_block_sizes)):
            block_size = cascade.get_block_size(qber, i)
            self.assertEqual(block_size, expected_block_sizes[i])

    def test_shuffle_block(self):
        # Ensures that shuffling results are reproduceable for test.
        random.seed(1034)

        block = [1, 1, 0, 1, 0]
        shuffled_block, shuffled_indices = cascade.shuffle_block(block)

        self.assertEqual(shuffled_block, [1, 0, 1, 0, 1])
        self.assertEqual(shuffled_indices, [0, 4, 3, 2, 1])

    def test_split_block(self):
        block = [0, 0, 1, 1, 1]

        left_block, right_block = cascade.split_block(block)

        self.assertEqual(left_block, [0, 0, 1])
        self.assertEqual(right_block, [1, 1])

    def test_get_block_parity(self):
        even_block = [0, 1, 1, 0, 0]
        odd_block = [0, 1, 1, 0, 1]

        parity = cascade.get_block_parity(even_block)
        self.assertEqual(parity, 0)

        parity = cascade.get_block_parity(odd_block)
        self.assertEqual(parity, 1)

    def test_get_error_parity(self):
        current_parities = [0, 0, 1, 1]
        correct_parities = [0, 1, 0, 1]
        expected_error_parities = [0, 1, 1, 0]

        for i in range(len(current_parities)):
            current_parity = current_parities[i]
            correct_parity = correct_parities[i]
            expected_error_parity = expected_error_parities[i]

            actual_error_parity = cascade.get_error_parity(
                current_parity,
                correct_parity,
            )

            self.assertEqual(
                actual_error_parity,
                expected_error_parity,
            )

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

    def test_ask_block_parity(self):
        socket = FakeSocket()
        socket.send = MagicMock()
        socket.recv = MagicMock(return_value="0")

        parity = cascade.ask_block_parity([3, 1, 2], socket)
        socket.send.assert_called_with("3,1,2")
        self.assertEqual(parity, 0)

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

        socket = FakeSocket()
        socket.send = MagicMock()
        socket.recv = MagicMock()

        socket.recv.side_effect = [1]

        # Demonstrate correcting a bit.
        result = cascade.binary_algorithm(
            left_block,
            left_block_indices,
            socket,
        )
        self.assertEqual(result, [0, 1, 1])

if __name__ == "__main__":
    unittest.main()
