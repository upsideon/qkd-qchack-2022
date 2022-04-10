from random import randint, sample

def measure_epr_in_random_bases(conn, epr_socket, num_epr_pairs, create_epr=True):
    """
    Measures EPR pairs in random measurement bases.

    Arguments:

    conn - A NetQASMConnection.
    epr_socket - An EPR socket.
    num_epr_pairs - The number of EPR pairs to create or receive.
    create_epr - Determines whether or not to create or receive EPR pairs.

    Returns:

    measurements - A list containing a measurement for each pair.
    measurement_bases - A list containing the measurement basis used for each pair.
    """

    measurements = []
    measurement_bases = []

    for i in range(num_epr_pairs):
        q = None

        if create_epr:
            # Creating entangled pairs.
            q = epr_socket.create_keep(1)[0]
        else:
            # Receiving entangled pairs.
            q = epr_socket.recv_keep(1)[0]

        # Selecting a random basis and measuring.
        basis = randint(0, 1)
        if basis == 1:
            q.H()
        m = q.measure()

        # Recording measurement.
        measurements.append(m)

        # Recording measurement basis.
        measurement_bases.append(basis)

        # Flushing commands.
        conn.flush()

    return measurements, measurement_bases

def publish_measurement_bases(measurement_bases, socket): 
    """
    Publishes measurement bases on a socket.
    """
    str_bases = [str(basis) for basis in measurement_bases]
    message = "".join(str_bases)
    socket.send(message)

def publish_subset_indices(indices, socket):
    """
    Publishes a subset's indices.
    """

    # Formatting and sending indices.
    str_indices = [str(i) for i in indices]
    indices_message = ",".join(str_indices)
    socket.send(indices_message)

def publish_subset_values(values, socket):
    """
    Publishes a subset's values.
    """

    # Formatting and sending values.
    str_values = [str(v) for v in values]
    values_message = "".join(str_values)
    socket.send(values_message)

def receive_measurement_bases(socket):
    """
    Receives measurement bases on a socket.
    """
    message = socket.recv()
    measurement_bases = list(message)
    return [int(bit) for bit in measurement_bases]

def receive_subset_indices(socket):
    """
    Receives subset indices on a socket.
    """
    message = socket.recv()
    str_indices = message.split(",") 
    return [int(i) for i in str_indices]

def receive_subset_values(socket):
    """
    Receives subset values on a socket.
    """
    message = socket.recv()
    return [int(v) for v in message]

def derive_raw_key(local_bases, remote_bases, measurements):
    """
    Derives a raw key from the bits where the chosen measurement bases
    were the same for both parties.
    """
    raw_key = []

    # Filtering out bits where measurement bases differed.
    for i in range(len(measurements)):
        local_basis = local_bases[i]
        remote_basis = remote_bases[i]

        if local_basis == remote_basis:
            raw_key.append(measurements[i])

    return raw_key

def get_random_raw_key_subset(raw_key, target_key_length):
    """
    Returns the indices and values for a random subset of the raw key.
    """
    raw_key_size = len(raw_key)
    subset_size = raw_key_size - target_key_length

    subset_indices = sample(
        [*range(raw_key_size)],
        k=subset_size,
    ) 
    subset_values = [raw_key[i] for i in subset_indices]

    return subset_indices, subset_values

def filter_comparison_bits(raw_key, comparison_subset_indices):
    """
    Filters comparison bits from raw key to produce a final secret key.
    """
    secret_key_bits = []

    for i in range(len(raw_key)):
        if not i in comparison_subset_indices:
            secret_key_bits.append(raw_key[i])

    return secret_key_bits
