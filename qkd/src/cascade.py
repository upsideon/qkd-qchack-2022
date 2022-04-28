import numpy as np

def quantum_bit_error_rate(local_set, remote_set):
    """
    Estimates the quantum bit error rate based on two sets.
    """
    num_incorrect = 0
    for i in range(len(local_set)):
        if remote_set[i] != local_set[i]:
            num_incorrect += 1
    return num_incorrect / len(local_set)

def binary_algorithm(block, block_indices, ask_parity_fn):
    """
    Recursively splits a block with odd error parity into
    left and right sub-blocks to find and correct one-bit
    errors.
    """

    # If we have a block of size one, we correct the bit as
    # it must have an odd number of errors per the input
    # assumptions of the binary algorithm.
    if len(block) == 1:
        if block[0] == 0:
            block[0] = 1
        else:
            block[0] = 0
        return block

    # The block split index selection ensures that the left
    # block has one more bit than the right when the block
    # size is odd.
    block_split_index = (len(block) + 1) // 2

    left_block = block[:block_split_index]
    right_block = block[block_split_index:]

    left_block_indices = block_indices[:block_split_index]
    right_block_indices = block_indices[block_split_index:]

    # Computing the current parity of the left block.
    current_left_block_parity = np.sum(left_block) % 2

    # Asking for the correct parity of the left block. The
    # parity of the right block can be inferred from the left
    # block's parity.
    correct_left_block_parity = ask_parity_fn(left_block_indices)

    # Determining the error parity for the left block.
    left_block_error_parity = current_left_block_parity ^ correct_left_block_parity

    # Recursing on the block with odd error parity.
    if left_block_error_parity == 1:
        left_block = binary_algorithm(left_block, left_block_indices, ask_parity_fn)
    else:
        right_block = binary_algorithm(right_block, right_block_indices, ask_parity_fn)

    return np.concatenate((left_block, right_block))

def client_cascade(noisy_key, qber, ask_parity_fn):
    """
    An implementation of the Cascade information reconciliation algorithm
    used for post-processing of keys exchanged via quantum key distribution.
    """

    # Representing the noisy key as a NumPy array, if it isn't already.
    noisy_key = np.array(noisy_key)

    key_length = len(noisy_key)

    # If the estimated quantum bit error rate is 0%, assume that a reasonable
    # amount of errors were present outside of the sampling set.
    if qber == 0.0:
        qber = 0.1

    # The top level block size is determined by the quantum bit error rate.
    block_size = int(np.round(0.73 / qber))

    iteration = 0

    while block_size <= key_length:
        # The identity permutation is used for the first iteration.
        permutation = np.arange(key_length)

        if iteration > 0:
            # Randomly shuffle Bob's key.
            rng = np.random.default_rng()
            permutation = rng.permutation(key_length)
            shuffled_key = noisy_key[permutation]

            # Increasing block size for current iteration.
            block_size *= 2
        else:
            # The key is not shuffled during the first iteration.
            shuffled_key = noisy_key.copy()

        num_blocks = int(np.ceil(key_length / block_size))

        for block_index in range(num_blocks):
            block = None
            block_indices = None

            block_start = block_size * block_index

            if block_index < num_blocks - 1:
                block_end = block_size * (block_index + 1)

                block = shuffled_key[block_start:block_end]
                block_indices = permutation[block_start:block_end]
            else:
                # The final block is not guaranteed to have the exact block size.
                block = shuffled_key[block_start:]
                block_indices = permutation[block_start:]

            # Computing current block parity.
            current_block_parity = np.sum(block) % 2

            # Requesting correct block parity.
            correct_block_parity = ask_parity_fn(block_indices)

            # Determining error parity.
            error_parity = current_block_parity ^ correct_block_parity

            # Correcting one-bit errors for blocks with odd error parity.
            if error_parity == 1:
                updated_block = binary_algorithm(block, block_indices, ask_parity_fn)
                noisy_key[block_indices] = updated_block

        iteration += 1

    return noisy_key

def get_ask_block_parity_fn(secret_key, socket):
    """
    Returns a function for requesting block parities that is compatible
    with the signature expected by client_cascade, but which communicates
    over a NetQasm socket.
    """

    secret_key = np.array(secret_key)

    def ask_block_parity(block_indices):
        request = ",".join([str(b) for b in list(block_indices)])

        socket.send(request)

        response = socket.recv()

        return int(response)

    return ask_block_parity

def get_block_parity_from_indices(full_key, indices):
    """
    Returns the parity of a subset of a key using indices.
    """
    element_sum = 0
    for i in indices:
        element_sum += full_key[i]
    return element_sum % 2

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
