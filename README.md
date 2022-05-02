# QuTech Quantum Network Explorer QKD Challenge

This repository contains my solution to QuTech's [Quantum Network Explorer](https://www.quantum-network.com) Quantum Key Distribution Challenge. Details on the challenge are given [here](CHALLENGE.md).

The original solution submitted to the hackathon can be viewed [here](https://github.com/upsideon/qkd-qchack-2022/tree/qchack-2022). Although the solution received [second place](https://www.quantumcoalition.io/winners-2022) it wasn't especially polished given the 24 hour time frame. In particular, although the BBM92 quantum key distribution algorithm was implemented successfully, my attempt at implementing the Cascade information reconciliation protocol as a post-processing step failed. Following the judging period, I was able to produce a working Cascade implementation. This and other updates are covered in the solution description.

Many thanks to the organizers and sponsors of QCHack 2022 for an excellent hacking experience! Thank you in particular to QuTech for creating a challenge that pushed me to dive into the world of quantum key distribution!

## Quantum Key Distribution Solution

This solution implements the [BBM92](https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.68.557) quantum key distribution algorithm. Keys are exchanged via entangled pairs sent over a simulated network created via QuTech's Quantum Network Explorer and interfaced with via the [NetQASM](https://github.com/QuTech-Delft/netqasm) library. In a noiseless environment, BBM92 is sufficient for key distribution as we are guaranteed that Alice and Bob with share the same key by the end of the process (assuming that eavesdropping has not occurred). Real world quantum networks are noisy, so this proves to be insufficient if we don't carry out some form of information reconciliation.

In this solution, the Cascade protocol is used as a classical post-processing step for information reconciliation. Assuming that Alice is the party with the correct key, Cascade allows Bob to correct his key in a way that reveals the least amount of information to an eavesdropper on the classical channel. Here, the protocol is implemented in such a way that it is not dependent on a particular communication mechanism and instead takes in a function which implements network specific logic. In this way, the code can be adapted to use frameworks outside of the Quantum Network Explorer, if necessary.

### Dependencies

The main dependencies of this project are the Quantum Network Explorer for simulating quantum networking environments and NumPy which facilitates an efficient and concise implementation of the Cascade protocol. To install the dependencies, execute `pip install -r requirements.txt`.

At the time of writing, installing the version of Quantum Network Explorer used in this repository requires a NetSquid forum account for accessing the Python package index hosted by QuTech. Anyone can register for an account [here](https://forum.netsquid.org/).

### Executing Experiments

All experiments can be run by executing `python autocheck.py`. The first experiment tests quantum key distribution in a noiseless environment, while the second experiment Cascade information reconciliation protocol in a noisy environment. Following experimentation, results can be found in `basic-experiment/results/processed.json` and `noise-experiment/results/processed.json`.

### Eavesdropper Configuration

The precense of an eavesdropper can be toggled on and off by updating the default value of the `eavesdropper` configuration option found in `qkd/config/application.json`. A value of one triggers eavesdropping, while a value of zero ensures the absence of an eavesdropper.

### Tests

Tests were written for portions of the Cascade information reconciliation algorithm and they can be run by executing `python qkd/src/test_cascade.py`.

### References

At the beginning of QCHack 2022, I was a novice in the domain of quantum key distribution. As such, I had to learn quite a bit rather quickly and I would have been hard pressed to get as far as I did without the help of the following resources:

* Bennett, Charles H., Gilles Brassard, and N. David Mermin. "Quantum cryptography without Bell’s theorem." Physical review letters 68.5 (1992): 557.

* Dahlberg, Axel, et al. "NetQASM--A low-level instruction set architecture for hybrid quantum-classical programs in a quantum internet." arXiv preprint arXiv:2111.09823 (2021).

* Ekert, Artur K. "Quantum Cryptography and Bell’s Theorem." Quantum Measurements in Optics. Springer, Boston, MA, 1992. 413-418.

* Erven, Chris. On free space quantum key distribution and its implementation with a polarization-entangled parametric down conversion source. MS thesis. University of Waterloo, 2007.

* Elkouss, David, Jesus Martinez-Mateo, and Vicente Martin. "Information reconciliation for quantum key distribution." arXiv preprint arXiv:1007.1616 (2010).

* Fung, Chi-Hang Fred, Xiongfeng Ma, and H. F. Chau. "Practical issues in quantum-key-distribution postprocessing." Physical Review A 81.1 (2010): 012318.

* Rijsman, Bruno. “A Cascade Information Reconciliation Tutorial.” Hiking and Coding, 15 Jan. 2020, [https://hikingandcoding.wordpress.com/2020/01/15/a-cascade-information-reconciliation-tutorial/](https://hikingandcoding.wordpress.com/2020/01/15/a-cascade-information-reconciliation-tutorial/). Accessed 10 Apr. 2022.

In particular, I'd like to especially highlight the [Cascade tutorial](https://hikingandcoding.wordpress.com/2020/01/15/a-cascade-information-reconciliation-tutorial/) by Bruno Rijsman. The research papers were very helpful in implementation of BBM92, but when it came to understanding Cascade, this blog post provides the best explanation I've encountered.
