from netqasm.sdk.qubit import Qubit

class Eve:

    def __init__(self):
        pass

    def eavesdrop(self, qubit: Qubit):
        # Measuring qubits as the eavesdropper.
        qubit.measure(inplace=True)
