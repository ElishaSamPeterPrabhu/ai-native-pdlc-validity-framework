"""Factor registry: the toggleable setup elements whose value is measured by ablation.

Each factor declares its pipeline stage, its toggle mechanism (how an experiment arm
turns it ON or OFF), and how its activity telemetry is derived from a run record.
The formula's recovery term (theory/formula.py DEFAULT_REGISTRY) mirrors these names;
this module is the operational side: it tells the driver what to do and the collector
what to record.
"""

from .registry import FACTORS, FactorDef, ToggleKind, arm_config, validate_arm
