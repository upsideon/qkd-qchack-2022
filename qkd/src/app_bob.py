import logging

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

import cascade
import util

logger = get_netqasm_logger()

def main(app_config=None, eavesdropper=False, key_length=16):
    # Ensuring that logs can be visualized following experiment.
    fileHandler = logging.FileHandler("bob_logfile.log")
    logger.setLevel(logging.INFO)
    logger.addHandler(fileHandler)

    # Socket for classical communication
    socket = Socket("bob", "alice", log_config=app_config.log_config)
    # Socket for EPR generation
    epr_socket = EPRSocket("alice", eavesdrop=eavesdropper)

    bob = NetQASMConnection(
        app_name=app_config.app_name,
        log_config=app_config.log_config,
        epr_sockets=[epr_socket],
    )

    secret_key = None
    num_epr_pairs = key_length * 3

    with bob:
        # Receiving and measuring EPR pairs in random bases.
        measurements, measurement_bases = util.measure_epr_in_random_bases(
            bob,
            epr_socket,
            num_epr_pairs,
            create_epr=False,
        )

        # Converting measurements into integers.
        measurements = [int(x) for x in measurements]

        # Publishing measurement bases.
        util.publish_measurement_bases(measurement_bases, socket)

        # Receiving measurement bases from the other side.
        received_measurement_bases = util.receive_measurement_bases(socket)

        # The raw key consists of all bits where the chosen
        # measurement bases were the same for both parties.
        raw_key = util.derive_raw_key(
                measurement_bases,
                received_measurement_bases,
                measurements,
        )

        # Receiving the indices of a random subset of the raw key.
        random_bit_indices = util.receive_subset_indices(socket)
        remote_random_subset = util.receive_subset_values(socket)

        # Determining the local random subset corresponding to indices.
        local_random_subset = [
            raw_key[int(i)] for i in random_bit_indices
        ]

        # Sending local random subset for comparison.
        util.publish_subset_values(local_random_subset, socket)

        # Determining the quantum bit error rate. If it is
        # above the threshold, do not return a key as this
        # indicates eavesdropping. Otherwise, go through the
        # Cascade information reconciliation algorithm.
        qber = cascade.quantum_bit_error_rate(
            local_random_subset,
            remote_random_subset,
        )

        # According to Erven 2007, the upper bound for a QBER that
        # should be identified as noise instead of eavesdropping is
        # 14.6%. Here we round to 15%.
        if qber < 0.15:
            secret_key_bits = []

            # Filtering out the bits sent for comparison.
            secret_key_bits = util.filter_comparison_bits(
                raw_key,
                random_bit_indices,
            )

            if len(secret_key_bits) > 0:
                secret_key = secret_key_bits

            # Ask questions to Alice until the Cascade information
            # reconciliation algorithm has terminated.
            ask_parity_fn = cascade.get_ask_block_parity_fn(secret_key, socket)
            secret_key = cascade.client_cascade(secret_key, qber, ask_parity_fn)
            cascade.send_cascade_stop(socket)

            # Converting NumPy array representation back into a list representation
            # to make it compatible with the auto-checking code.
            secret_key = secret_key.tolist()
        else:
            secret_key = None

    return {
        "secret_key": secret_key,
    }


if __name__ == "__main__":
    main()
