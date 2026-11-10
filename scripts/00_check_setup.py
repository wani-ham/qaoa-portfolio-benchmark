import math
import os
import warnings
import qiskit, qiskit_aer, qiskit_ibm_runtime
from dotenv import load_dotenv
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService
from pulser import Register, Sequence, Pulse
from pulser.devices import AnalogDevice
from pulser.backend import BitStrings
from pulser_simulation import QutipBackendV2, QutipConfig
from pulser.backends import QPUBackend
from qpb.credentials import pasqal_connection

load_dotenv()

print("qiskit", qiskit.__version__, "| aer", qiskit_aer.__version__,
      "| runtime", qiskit_ibm_runtime.__version__)

# IBM - Local Simulator Test
qc = QuantumCircuit(2)
qc.h(0); qc.cx(0, 1); qc.measure_all()
simulator = AerSimulator()
result = simulator.run(qc, shots=1000).result().get_counts()
print("Bell Counts: ", result)

# IBM - Cloud account check
instance = os.getenv("IBM_QUANTUM_INSTANCE", "")
if not instance or "..." in instance:
    instance = "auto"
service = QiskitRuntimeService(instance=instance)
for b in service.backends():
    print("IBM backend:", b.name, b.num_qubits, "qubits")

# PASQAL - Pulser Emulator Test
reg = Register({"q0": (0, 0), "q1": (6, 0)})          # 6 micrometres apart
seq = Sequence(reg, AnalogDevice)
seq.declare_channel("ryd", "rydberg_global")
omega = 6.283                                          # Rabi frequency, rad/µs
seq.add(Pulse.ConstantPulse(352, omega, 0, 0), "ryd") # ~ π pulse for the blockaded pair, in ns
config = QutipConfig(observables=[BitStrings(num_shots=1000)])
res = QutipBackendV2(seq, config=config).run()
print("Pulser blockade counts:", res.final_bitstrings)

# PASQAL - QPU account check
conn = pasqal_connection()
# Pasqal's device specs still use the old `NoiseModel.runs` field, which makes
# Pulser warn on load. It's in their data, not our code, so hide just that message.
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", message=".*NoiseModel.runs.*", category=DeprecationWarning)
    devices = conn.fetch_available_devices()
print("Pasqal devices:", list(devices))
device = devices["FRESNEL"]

# Real devices place atoms only on pre-calibrated trap layouts, and each layout
# must be at least `min_layout_filling` full (FRESNEL: 35% of 120 traps = 42 atoms),
# so a 2-atom test can't run on the QPU. Build the smallest valid register instead.
layout = device.pre_calibrated_layouts[0]
n_atoms = math.ceil(device.min_layout_filling * layout.number_of_traps)
reg = layout.define_register(*range(n_atoms))

seq = Sequence(reg, device)                # raises if the register breaks device rules
seq.declare_channel("ryd", "rydberg_global")
seq.add(Pulse.ConstantPulse(352, 6.283, 0, 0), "ryd")
seq.measure("ground-rydberg")

# Building the backend validates the sequence against the cloud; nothing is submitted.
# To run on hardware (uses credits): qpu.run(job_params=[{"runs": 100}], wait=True)
qpu = QPUBackend(seq, connection=conn)
print(f"Pasqal {device.name}: {n_atoms}-atom sequence is valid (not submitted)")
