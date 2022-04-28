import logging

from netqasm.logging.glob import get_netqasm_logger
from netqasm.sdk.external import NetQASMConnection, Socket

from epr_socket import DerivedEPRSocket as EPRSocket

import cascade
import util

logger = get_netqasm_logger()

def main(app_config=None, eavesdropper=False, key_length=16):
    # Ensuring that logs can be visualized following experiment.
    fileHandler = logging.FileHandler("alice_logfile.log")
    logger.setLevel(logging.INFO)
    logger.addHandler(fileHandler)

    # Socket for classical communication
    socket = Socket("alice", "bob", log_config=app_config.log_config)
    # Socket for EPR generation
    epr_socket = EPRSocket("bob", eavesdrop=eavesdropper)

    alice = NetQASMConnection(
        app_name=app_config.app_name,
        log_config=app_config.log_config,
        epr_sockets=[epr_socket],
    )

    secret_key = None
    num_epr_pairs = key_length * 3

    with alice:
        # Generating and measuring EPR pairs in random bases.
        measurements, measurement_bases = util.measure_epr_in_random_bases(
            alice,
            epr_socket,
            num_epr_pairs,
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

        # Determining a random subset of the raw key to compare.
        random_bit_indices, random_subset = util.get_random_raw_key_subset(
            raw_key,
            key_length,
        )

        # Sending random subset indices and values.
        util.publish_subset_indices(random_bit_indices, socket)
        util.publish_subset_values(random_subset, socket)

        # Receiving remote subset for comparison.
        remote_subset = util.receive_subset_values(socket)

        # Determining the quantum bit error rate. If it is
        # above the threshold, do not return a key as this
        # indicates eavesdropping. Otherwise, go through the
        # Cascade information reconciliation algorithm.
        qber = cascade.quantum_bit_error_rate(
            random_subset,
            remote_subset,
        )

        # According to Erven 2007, the upper bound for a QBER that
        # should be identified as noise instead of eavesdropping is
        # 14.6%. Here we round to 20%.
        if qber < 0.2:
            secret_key_bits = []

            # Filtering out the bits sent for comparison.
            secret_key_bits = util.filter_comparison_bits(
                raw_key,
                random_bit_indices,
            )

            if len(secret_key_bits) > 0:
                secret_key = secret_key_bits

            # Answer questions from Bob until the Cascade information
            # reconciliation algorithm has terminated.
            cascade.listen_and_respond_block_parity(secret_key, socket)
        else:
            secret_key = None

    return {
        "secret_key": secret_key,
    }


if __name__ == "__main__":
    main()
