import os
import shutil
import subprocess
from typing import Dict, List, Optional

from test_case import TestCase

KEY_LENGTH = 16

class BasicProtocolsTestCase(TestCase):

    def __init__(self, key_length):
        super().__init__("Basic protocols", key_length)

    def _configure_test_case(self, experiment: Dict) -> None:
        # Configuring for eavesdropping, if present in configuration.
        app_config = experiment["asset"]["application"]
        eavesdrop_config = app_config[1]["values"][0]
        eavesdrop = eavesdrop_config["value"]
        self.eavesdrop = eavesdrop

    def _verify_test_case(
            self,
            alice_secret_key: Optional[List[int]],
            bob_secret_key: Optional[List[int]]
    ) -> TestCase.Result:

        if alice_secret_key is None:
            if not self.eavesdrop:
                return TestCase.Result(
                    success=False,
                    message=(
                        "Alice and/or Bob did not generate a secret key "
                        "even though no eavesdropper was present"
                    ),
                )

        return TestCase.Result(success=True, message=None)

class CascadeProtocolTestCase(TestCase):

    def __init__(self, key_length):
        super().__init__("Cascade Protocol", key_length)

    def _configure_test_case(self, experiment: Dict) -> None:
        # Configuring for eavesdropping, if present in configuration.
        app_config = experiment["asset"]["application"]
        eavesdrop_config = app_config[1]["values"][0]
        eavesdrop = eavesdrop_config["value"]
        self.eavesdrop = eavesdrop

        network_channels = experiment["asset"]["network"]["channels"]

        # Updating the fidelity on one of the network channels to
        # introduce noise. If the Cascade information reconciliation
        # process is correctly implemented, it should be able to
        # correct this level of noise.
        for network_channel in network_channels:
            if network_channel["slug"] == "amsterdam-leiden":
                parameters = network_channel["parameters"]
                for parameter in parameters:
                    if parameter["slug"] == "elementary-link-fidelity":
                        values = parameter["values"]
                        for value in values:
                            if value["name"] == "fidelity":
                                value["value"] = 0.9

    def _verify_test_case(
            self,
            alice_secret_key: Optional[List[int]],
            bob_secret_key: Optional[List[int]]
    ) -> TestCase.Result:

        if self.eavesdrop:
            if alice_secret_key is not None or bob_secret_key is not None:
                return TestCase.Result(
                    success=False,
                    message=(
                        "A secret key was returned despite eavesdropping"
                    ),
                )

        if alice_secret_key != bob_secret_key:
            return TestCase.Result(
                success=False,
                message=(
                    "Alice and Bob do not share the same secret key"
                ),
            )

        return TestCase.Result(success=True, message=None)


def run(test: TestCase, timeout: int = 60) -> bool:
    test.configure()

    result = subprocess.run(
        ["qne", "experiment", "run", "--timeout", str(timeout)],
        stdout=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError("Experiment run failed")

    return test.verify()

experiments = [
    {
        "name": "basic-experiment",
        "test_case": BasicProtocolsTestCase,
    },
    {
        "name": "noise-experiment",
        "test_case": CascadeProtocolTestCase,
    },
]

def main():
    for experiment in experiments:
        experiment_name = experiment["name"]

        if os.path.exists(experiment_name):
            shutil.rmtree(experiment_name)

        result = subprocess.run(
            ["qne", "experiment", "create", experiment_name, "qkd", "randstad"],
            stdout=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            raise RuntimeError("Experiment creation failed")

        os.chdir(experiment_name)

        success = run(experiment["test_case"](KEY_LENGTH))

        os.chdir("..")

    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
