"""Canonical JEE Physics syllabus taxonomy — the seed of the knowledge graph.

Each chapter carries:
  keywords : distinctive vocabulary for the offline keyword classifier
  concepts : {concept_name: [keywords]} for finer, concept-level tagging

The LLM tagger is CONSTRAINED to these chapter names (no free-text drift), and the
offline fallback scores questions against these keywords. Extend per exam/subject
by adding a sibling taxonomy (NEET Biology, Class-12 Chemistry, …)."""

JEE_PHYSICS = {
    "Units, Dimensions & Measurement": {
        "keywords": ["dimensional", "significant figure", "least count", "vernier",
                     "screw gauge", "fractional error", "percentage error", "measurement",
                     "error in", "uncertainty"],
        "concepts": {
            "Error Analysis": ["fractional error", "percentage error", "uncertainty", "error in"],
            "Dimensional Analysis": ["dimensional", "dimensions of"],
            "Measuring Instruments": ["vernier", "screw gauge", "least count"],
        },
    },
    "Kinematics": {
        "keywords": ["projectile", "displacement", "velocity", "acceleration",
                     "relative velocity", "trajectory", "range of the projectile"],
        "concepts": {
            "Projectile Motion": ["projectile", "range", "trajectory"],
            "Motion in a Straight Line": ["uniform acceleration", "displacement", "retardation"],
        },
    },
    "Laws of Motion": {
        "keywords": ["friction", "normal reaction", "tension", "inclined plane",
                     "free body", "coefficient of friction", "pulley", "reaction force"],
        "concepts": {
            "Friction": ["friction", "coefficient of friction"],
            "Newton's Laws / Equilibrium": ["reaction force", "normal reaction", "tension", "equilibrium"],
        },
    },
    "Work, Energy & Power": {
        "keywords": ["work done", "kinetic energy", "potential energy", "conservation of energy",
                     "power delivered", "work-energy"],
        "concepts": {
            "Energy Conservation": ["conservation of energy", "potential energy", "kinetic energy"],
            "Work & Power": ["work done", "power delivered"],
        },
    },
    "Rotational Motion": {
        "keywords": ["moment of inertia", "torque", "angular momentum", "angular velocity",
                     "rolling", "rigid body", "centre of mass", "center of mass",
                     "uniform stick", "rotational", "angular acceleration"],
        "concepts": {
            "Moment of Inertia": ["moment of inertia"],
            "Torque & Equilibrium of Rigid Body": ["torque", "uniform stick", "rigid body", "reaction of the wall"],
            "Angular Momentum": ["angular momentum", "angular velocity"],
            "Rolling Motion": ["rolling"],
        },
    },
    "Gravitation": {
        "keywords": ["gravitational", "escape velocity", "orbital velocity", "satellite",
                     "kepler", "gravity", "planet", "gravitational potential", "sun", "orbit of"],
        "concepts": {
            "Orbital & Escape Velocity": ["escape velocity", "orbital velocity", "satellite"],
            "Kepler's Laws": ["kepler", "planet", "orbit of"],
        },
    },
    "Properties of Matter & Fluids": {
        "keywords": ["young's modulus", "elasticity", "surface tension", "viscosity",
                     "bernoulli", "pressure", "bulk modulus", "capillary", "stress", "strain",
                     "density of the sphere", "expanding sphere"],
        "concepts": {
            "Elasticity": ["young's modulus", "bulk modulus", "stress", "strain", "elasticity"],
            "Fluid Mechanics": ["bernoulli", "viscosity", "surface tension", "capillary"],
        },
    },
    "Thermodynamics & Kinetic Theory": {
        "keywords": ["thermodynamic", "isothermal", "adiabatic", "carnot", "entropy",
                     "specific heat", "ideal gas", "internal energy", "heat engine",
                     "degrees of freedom", "mean free path", "furnace", "radiated"],
        "concepts": {
            "Laws of Thermodynamics": ["isothermal", "adiabatic", "internal energy", "carnot", "heat engine"],
            "Kinetic Theory": ["degrees of freedom", "mean free path", "rms speed"],
            "Thermal Radiation": ["radiated", "furnace", "stefan", "black body"],
        },
    },
    "Oscillations (SHM)": {
        "keywords": ["simple harmonic", "oscillation", "pendulum", "spring constant",
                     "angular frequency", "amplitude", "restoring force", "time period"],
        "concepts": {
            "Simple Harmonic Motion": ["simple harmonic", "restoring force", "amplitude"],
            "Pendulum & Springs": ["pendulum", "spring constant"],
        },
    },
    "Waves & Sound": {
        "keywords": ["wave", "frequency", "wavelength", "resonance", "beats", "doppler",
                     "sound", "standing wave", "harmonic", "velocity of sound", "string"],
        "concepts": {
            "Sound & Doppler": ["doppler", "velocity of sound", "sound"],
            "Standing Waves / Resonance": ["resonance", "standing wave", "harmonic", "string"],
        },
    },
    "Electrostatics": {
        "keywords": ["electric field", "electric potential", "charge", "capacitor",
                     "coulomb", "dipole", "gauss", "flux", "capacitance", "dielectric"],
        "concepts": {
            "Coulomb's Law & Field": ["coulomb", "electric field", "dipole"],
            "Capacitors": ["capacitor", "capacitance", "dielectric"],
            "Gauss's Law": ["gauss", "flux"],
        },
    },
    "Current Electricity": {
        "keywords": ["resistor", "resistance", "current", "kirchhoff", "wheatstone",
                     "emf", "internal resistance", "potentiometer", "ohm", "circuit"],
        "concepts": {
            "DC Circuits": ["kirchhoff", "wheatstone", "resistor", "circuit"],
            "EMF & Internal Resistance": ["emf", "internal resistance", "potentiometer"],
        },
    },
    "Magnetism & Moving Charges": {
        "keywords": ["magnetic field", "lorentz", "cyclotron", "solenoid", "biot",
                     "ampere", "magnetic moment", "charged particle in a magnetic"],
        "concepts": {
            "Force on Moving Charge": ["lorentz", "cyclotron", "charged particle in a magnetic"],
            "Magnetic Field of Currents": ["biot", "ampere", "solenoid"],
        },
    },
    "Electromagnetic Induction & AC": {
        "keywords": ["induced emf", "faraday", "lenz", "inductance", "alternating",
                     "impedance", "reactance", "rms", "lc circuit", "transformer",
                     "voltmeter", "ac source"],
        "concepts": {
            "Electromagnetic Induction": ["faraday", "lenz", "induced emf", "inductance"],
            "Alternating Current": ["impedance", "reactance", "rms", "ac source", "voltmeter"],
        },
    },
    "Ray Optics": {
        "keywords": ["refraction", "lens", "mirror", "prism", "total internal reflection",
                     "focal length", "refractive index", "magnification"],
        "concepts": {
            "Reflection & Refraction": ["mirror", "refraction", "refractive index", "prism"],
            "Lenses": ["lens", "focal length", "magnification"],
        },
    },
    "Wave Optics": {
        "keywords": ["interference", "diffraction", "young's double slit", "fringe",
                     "polarization", "coherent", "path difference"],
        "concepts": {
            "Interference (YDSE)": ["interference", "young's double slit", "fringe", "path difference"],
            "Diffraction & Polarization": ["diffraction", "polarization"],
        },
    },
    "Modern Physics": {
        "keywords": ["photoelectric", "stopping potential", "work function", "planck",
                     "photon", "photoelectron", "de broglie", "bohr", "rydberg",
                     "quantum number", "hydrogen-like", "nucleus", "radioactive", "half-life",
                     "binding energy", "atomic", "emission spectrum", "wavelength of incident",
                     "principal quantum"],
        "concepts": {
            "Photoelectric Effect": ["photoelectric", "stopping potential", "work function", "photon", "photoelectron"],
            "Bohr Model & Atomic Spectra": ["bohr", "rydberg", "quantum number", "hydrogen-like", "emission spectrum", "principal quantum"],
            "Nuclear Physics": ["nucleus", "radioactive", "half-life", "binding energy", "decay"],
            "Dual Nature / de Broglie": ["de broglie", "matter wave"],
        },
    },
    "Semiconductors & Electronics": {
        "keywords": ["semiconductor", "diode", "transistor", "logic gate", "p-n junction",
                     "rectifier", "zener", "doping"],
        "concepts": {
            "Diodes & Rectifiers": ["diode", "rectifier", "zener", "p-n junction"],
            "Transistors & Logic Gates": ["transistor", "logic gate"],
        },
    },
}

from .jee_main_physics import JEE_MAIN_PHYSICS
from .jee_main_chemistry import JEE_MAIN_CHEMISTRY
from .jee_main_maths import JEE_MAIN_MATHS
from .neet_biology import NEET_BIOLOGY
from .neet_physics import NEET_PHYSICS
from .neet_chemistry import NEET_CHEMISTRY
from .banking_quant import BANKING_QUANT
from .icse_class3_maths import ICSE_CLASS3_MATHS

# Registry so other exams/subjects slot in with the same interface.
TAXONOMIES = {
    # ICSE Class 3 Maths (kids product) — real book chapters; without this it fell back to
    # the JEE Physics taxonomy (get_taxonomy default) and the kids picker showed Physics.
    ("ICSE Class 3", "Mathematics"): ICSE_CLASS3_MATHS,
    ("JEE Advanced", "Physics"): JEE_PHYSICS,
    ("JEE Main", "Physics"): JEE_MAIN_PHYSICS,
    ("JEE Main", "Chemistry"): JEE_MAIN_CHEMISTRY,
    ("JEE Main", "Mathematics"): JEE_MAIN_MATHS,
    # JEE Advanced Chem/Maths share the same syllabus chapters as JEE Main (harder
    # questions, same topics) — reuse the grafite-derived taxonomies for tagging.
    ("JEE Advanced", "Chemistry"): JEE_MAIN_CHEMISTRY,
    ("JEE Advanced", "Mathematics"): JEE_MAIN_MATHS,
    # NEET: all three subjects now have their own chapter taxonomies derived from the
    # datavorous NEET bank (the dominant source, ~40k Qs). NEET's chapter vocabulary
    # is NEET-specific — it does NOT match JEE Main's — so it must not reuse them.
    ("NEET", "Physics"): NEET_PHYSICS,
    ("NEET", "Chemistry"): NEET_CHEMISTRY,
    ("NEET", "Biology"): NEET_BIOLOGY,
    # Banking (IBPS/SBI/RRB) shared Prelims pattern. GENERATION-first: no ingested
    # exemplars — qbank.quantgen draws these chapters deterministically (compute-the-
    # answer). One taxonomy serves all banking exams; tag by `exam` at generation.
    ("Banking Prelims", "Quantitative Aptitude"): BANKING_QUANT,
}


# Where to borrow RAG exemplars when a chapter is thin in its own exam. NEET Physics/
# Chemistry USED to borrow from JEE Main (when we held only ~130 real NEET Qs each),
# but the datavorous ingest gave NEET its own deep bank (~5k Phy, ~13k Chem) under
# NEET-specific chapter names that do NOT match JEE Main's — so borrowing is now both
# unnecessary and wrong. Left empty; re-add an entry only for a genuinely thin subject.
EXEMPLAR_FALLBACK = {}


def get_taxonomy(exam: str, subject: str):
    return TAXONOMIES.get((exam, subject)) or TAXONOMIES.get(("JEE Advanced", "Physics"))


def exemplar_fallback(exam: str, subject: str):
    """(exam, subject) to borrow exemplars from, or None."""
    return EXEMPLAR_FALLBACK.get((exam, subject))
