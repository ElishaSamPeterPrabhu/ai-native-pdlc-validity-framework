"""Simulation lab for the validity formula.

Modules:
    trajectory   Monte Carlo agent-trajectory generator (synthetic telemetry)
    sensitivity  Sobol global sensitivity analysis over formula parameters
    identify     Identifiability check: fit the ODE to synthetic data, recover weights
    regimes      Regime maps: equilibrium validity and time-to-collapse figures

All model math is imported from theory/formula.py; nothing here redefines it.
"""

import os
import sys

_THEORY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "theory")
if _THEORY_DIR not in sys.path:
    sys.path.insert(0, _THEORY_DIR)
