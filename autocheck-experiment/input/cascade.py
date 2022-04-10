import math

from random import sample

def quantum_bit_error_rate(local_set, remote_set):
    """
    Estimates the quantum bit error rate based on two sets.
    """
    num_incorrect = 0
    for i in range(len(local_set)):
        if remote_set[i] != local_set[i]:
            num_incorrect += 1
    return num_incorrect / len(local_set)

def get_block_size(quantum_bit_error_rate, iteration):
    """
    Determines the appropriate block size given the QBER.
    """
    block_size = 0
    for i in range(iteration + 1):
        if i == 0:
            block_size = math.ceil(0.73 / quantum_bit_error_rate)
        else:
            block_size = 2 * block_size
    return block_size
        
def shuffle_block(block):
    """
    Randomly shuffles a block.

    Returns:

    shuffled_block - The shuffled block.
    unshuffled_indices - The original indices associated with shuffled elements.
    """
    indices = [*range(len(block))]
    shuffled_indices = sample(indices, k=len(indices))
    shuffled_block = [block[i] for i in shuffled_indices]
    return shuffled_block, shuffled_indices

def split_block(block):
    """
    Splits a block returning two sublocks of equal or nor equal size.
    """
    split_location = (len(block) + 1) // 2
    left_block = block[:split_location]
    right_block = block[split_location:]
    return left_block, right_block

def get_block_parity(block):
    """
    Returns the parity of a block.
    """
    return sum(block) % 2

def get_block_parity_from_indices(full_key, indices):
    """
    Returns the parity of a subset of a key using indices.
    """
    element_sum = 0
    for i in indices:
        element_sum += full_key[i]
    return element_sum % 2

def ask_block_parity(unshuffled_element_indices, socket):
    """
    Asks for the correct parity of a block.
    """
    message = ",".join([str(i) for i in unshuffled_element_indices])
    socket.send(message)

    response = socket.recv()
    return int(response)

def send_cascade_stop(socket):
    socket.send("STOP")

def listen_and_respond_block_parity(correct_key, socket):
    """
    Listens for block parity questions and responds.
    """
    question = socket.recv()

    while question != "STOP":
        block_indices = [int(s) for s in question.split(",")]
        correct_parity = get_block_parity_from_indices(
            correct_key,
            block_indices,
        )
        socket.send(str(correct_parity))
        question = socket.recv()

def get_error_parity(current_parity, correct_parity):
    """
    Returns the error parity based on current and correct parity.
    """
    return (current_parity + correct_parity) % 2

def binary_algorithm(block, indices, socket):
    """
    Applies the binary algorithm to a block with odd parity.
    This is a recursive process which results in a single bit
    correction.
    """
    if len(block) == 0:
        return block

    if len(block) == 1:
        block[0] = 1 if block[0] == 0 else 0
        return block

    left_block, right_block = split_block(block)
    left_block_indices, right_block_indices = split_block(indices)

    current_left_block_parity = get_block_parity(block)
    correct_left_block_parity = ask_block_parity(indices, socket)
    
    left_block_error_parity = get_error_parity(
        current_left_block_parity,
        correct_left_block_parity,
    )

    # Recursively apply the binary algorithm to sublocks with odd error parity.
    if left_block_error_parity == 1:
        binary_algorithm(left_block, left_block_indices, socket)
    else:
        binary_algorithm(right_block, right_block_indices, socket)

    return left_block + right_block

def cascade(key, qber, socket, logger=None):
    """
    Applies the Cascade information reconciliation algorithm to a key.
    """
    if qber == 0.0:
        qber = 0.1

    i = 0

    block_size = get_block_size(qber, i)
    shuffled_key = key.copy()
    indices = [*range(len(key))]

    while block_size <= len(key):
        num_blocks = len(key) // block_size

        # Only shuffling the key after the first iteration.
        if i > 0:
            shuffled_key, indices = shuffle_block(key)

        updated_shuffled_key = []

        # Processing blocks.
        for block_index in range(num_blocks):
            block_start = block_index * block_size
            block_end = (block_index + 1) * block_size

            if block_index == num_blocks - 1:
                leftovers = len(key) - num_blocks * block_size
                block_end += leftovers

            block = shuffled_key[block_start:block_end]
            block_indices = indices[block_start:block_end]

            current_parity = get_block_parity(block)
            correct_parity = ask_block_parity(block_indices, socket)
            error_parity = get_error_parity(
                current_parity,
                correct_parity,
            )

            if error_parity == 1:
                block = binary_algorithm(block, block_indices, socket)

            updated_shuffled_key += block

        updated_unshuffled_key = [-1] * len(key)

        for i in range(len(key)):
            updated_unshuffled_key[i] = key[indices[i]]

        i += 1

        block_size = get_block_size(qber, i)

        key = updated_unshuffled_key

    send_cascade_stop(socket)

    return key


