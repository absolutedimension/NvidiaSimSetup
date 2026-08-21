"""GP Rating (Synergy CET / merchant-navy ratings entry) taxonomy.

Grounded on the DG Shipping approved GP Ratings course structure (Training Circular 1
of 2018), as it actually appears in the MTI chapter banks we ingest: the source tags
every question with an opaque module code (`Chapter GSK 6`, `Chapter MEK 16`). Those
codes are useless in a student-facing picker, so `CODE_TO_CHAPTER` below maps each one
to a readable chapter name, and the names here are the EXACT `chapter` strings the pool
is stored under — so `/chapters` reports real counts and `/pool` serves them.

Two subjects, matching the two knowledge sections of the entrance paper:
  GSK -> "Ship Knowledge & Safety"  (navigation, cargo handling, safety)
  MEK -> "Marine Engineering"       (machinery operations, workshop practice, safety)

Chapter names were derived from the questions themselves, not guessed — each name
reflects what that module's stems are actually about.

⚠️ COVERAGE GAP, stated on purpose: the source bank is missing GSK 4 and
MEK 3/4/5/6/8/11/19 entirely. This is NOT the full DG syllabus. Do not market it as
"complete syllabus coverage". Those modules need a second source or grounded generation
from the DG circular text.

`keywords` drive the offline keyword tagger; `concepts` give the finer concept level.
Registered in syllabus.TAXONOMIES under ("Synergy CET", <subject>).
"""

# The source bank's module code -> (subject, readable chapter name).
# Ingest rewrites `chapter` through this map; anything unmapped is dropped loudly
# rather than banked under an opaque code.
CODE_TO_CHAPTER = {
    # ---- GSK: General Ship Knowledge (Section A) ----
    "GSK 1":  ("Ship Knowledge & Safety", "Communication & Shipboard Duties"),
    "GSK 2":  ("Ship Knowledge & Safety", "Ship Types & Parts of a Ship"),
    "GSK 3":  ("Ship Knowledge & Safety", "Safety Signs & Enclosed Spaces"),
    "GSK 5":  ("Ship Knowledge & Safety", "Basic Navigation, Charts & Flags"),
    "GSK 6":  ("Ship Knowledge & Safety", "Mooring & Anchoring"),
    "GSK 7":  ("Ship Knowledge & Safety", "Cargo Handling & Stowage"),
    "GSK 8":  ("Ship Knowledge & Safety", "Rope Work, Blocks & Safe Working Loads"),
    "GSK 9":  ("Ship Knowledge & Safety", "Safety, LSA & Emergency Procedures"),
    "GSK 10": ("Ship Knowledge & Safety", "Marine Regulations & Documentation"),
    # ---- MEK: Marine Engineering Knowledge (Section B) ----
    "MEK 1":  ("Marine Engineering", "Engine Room Layout & Machinery"),
    "MEK 2":  ("Marine Engineering", "Hand Tools & Fasteners"),
    "MEK 7":  ("Marine Engineering", "Diesel Engine Systems"),
    "MEK 9":  ("Marine Engineering", "Machine Tools & Workshop Practice"),
    "MEK 10": ("Marine Engineering", "Welding & Cutting"),
    "MEK 12": ("Marine Engineering", "Level Measurement & Sounding"),
    "MEK 13": ("Marine Engineering", "Insulation & Lagging"),
    "MEK 14": ("Marine Engineering", "Chemical Handling & Safety"),
    "MEK 15": ("Marine Engineering", "Steering Gear & Thrusters"),
    "MEK 16": ("Marine Engineering", "Tanks, Valves & Ballast Systems"),
    "MEK 17": ("Marine Engineering", "Engine Room Alarms & Emergency Response"),
    "MEK 18": ("Marine Engineering", "Fire Fighting Equipment"),
    "MEK 20": ("Marine Engineering", "Basic Electrical Safety"),
}


GP_RATING_GSK = {
    "Communication & Shipboard Duties": {
        "keywords": ["communication", "verbal", "non-verbal", "k-s-a-v", "ethical",
                     "duties of a deck rating", "teamwork", "chain of command",
                     "report to", "personal computer", "mouse", "keyboard"],
        "concepts": {
            "Modes of Communication": ["verbal", "non-verbal", "written", "mode of communication"],
            "Shipboard Hierarchy & Duties": ["duties", "deck rating", "chain of command", "report to"],
            "Work Ethics": ["ethical", "ethics", "attitude", "k-s-a-v"],
        },
    },
    "Ship Types & Parts of a Ship": {
        "keywords": ["type of ship", "bulk carrier", "tanker", "container", "hatch cover",
                     "fore mast", "accommodation", "bow", "stern", "windlass", "forecastle",
                     "superstructure", "double bottom", "sopep"],
        "concepts": {
            "Types of Vessels": ["bulk carrier", "tanker", "container", "type of ship", "gearless"],
            "Structural Parts": ["bow", "stern", "mast", "accommodation", "forecastle", "double bottom"],
            "Deck Equipment Upkeep": ["sopep", "lsa", "ffa", "winches", "cranes"],
        },
    },
    "Safety Signs & Enclosed Spaces": {
        "keywords": ["safety sign", "enclosed space", "permit to work", "welding",
                     "eye protection", "prohibition sign", "mandatory sign", "warning sign",
                     "confined space", "oxygen deficient"],
        "concepts": {
            "Safety Signage": ["safety sign", "prohibition", "mandatory", "warning sign"],
            "Enclosed Space Entry": ["enclosed space", "confined space", "permit to work", "oxygen"],
            "PPE": ["eye protection", "goggles", "helmet", "gloves"],
        },
    },
    "Basic Navigation, Charts & Flags": {
        "keywords": ["chart", "compass rose", "position", "plotted", "house flag",
                     "intercode flag", "pilot on board", "helm order", "wheel", "midships",
                     "latitude", "longitude", "bearing", "buoyage"],
        "concepts": {
            "Charts & Position": ["chart", "plotted", "compass rose", "latitude", "longitude"],
            "Flags & Signals": ["house flag", "intercode", "flag", "hoisted", "pilot on board"],
            "Helm Orders": ["helm", "wheel", "midships", "hard to port", "steady"],
        },
    },
    "Mooring & Anchoring": {
        "keywords": ["anchor", "aweigh", "cable", "scope of cable", "spurling pipe",
                     "bow stopper", "heaving line", "mooring", "windlass", "bitts",
                     "fairlead", "rope", "spring", "breast line"],
        "concepts": {
            "Anchoring": ["anchor", "aweigh", "cable", "scope", "spurling pipe", "bow stopper"],
            "Mooring Lines": ["heaving line", "mooring", "spring", "breast line", "bitts", "fairlead"],
            "Rope Types": ["rope no", "manila", "polypropylene", "wire rope"],
        },
    },
    "Cargo Handling & Stowage": {
        "keywords": ["cargo", "hatch cover", "lift on lift off", "stowage", "derrick",
                     "union purchase", "strum box", "sounding pipe cap", "gantry",
                     "container", "hold", "dunnage", "ship sweat", "grab"],
        "concepts": {
            "Hatch Covers": ["hatch cover", "lift on lift off", "rubber packing", "eccentric roller"],
            "Cargo Gear": ["derrick", "union purchase", "gantry", "crane", "grab", "sling"],
            "Stowage & Hold Prep": ["stowage", "hold", "dunnage", "strum box", "ship sweat"],
        },
    },
    "Rope Work, Blocks & Safe Working Loads": {
        "keywords": ["wire rope", "condemned", "splice", "back splice", "knot", "bowline",
                     "block", "purchase", "swl", "safe working load", "lead block",
                     "shackle", "sheave", "snatch block"],
        "concepts": {
            "Knots & Splices": ["knot", "splice", "back splice", "bowline", "temporary eye"],
            "Blocks & Purchases": ["block", "purchase", "lead block", "sheave", "snatch"],
            "Safe Working Load": ["swl", "safe working load", "condemned", "test certificate"],
        },
    },
    "Safety, LSA & Emergency Procedures": {
        "keywords": ["eebd", "lifeboat", "abandon ship", "solas", "muster", "life jacket",
                     "liferaft", "safety goggles", "gangway", "safe access", "immersion suit",
                     "distress", "fire drill", "man overboard"],
        "concepts": {
            "Life Saving Appliances": ["lifeboat", "liferaft", "life jacket", "immersion suit", "eebd"],
            "Emergency Drills": ["abandon ship", "muster", "drill", "man overboard", "distress"],
            "Safe Access & PPE": ["gangway", "safe access", "goggles", "harness"],
        },
    },
    "Marine Regulations & Documentation": {
        "keywords": ["dgs", "cdc", "marpol", "solas", "stcw", "shore pass", "immigration",
                     "official log book", "oil record book", "certificate", "port state",
                     "flag state", "seaman's book"],
        "concepts": {
            "Conventions": ["solas", "marpol", "stcw", "convention", "regulation"],
            "Documents & Certificates": ["cdc", "shore pass", "certificate", "seaman's book", "passport"],
            "Record Books": ["official log book", "oil record book", "sounding", "entered in"],
        },
    },
}


GP_RATING_MEK = {
    "Engine Room Layout & Machinery": {
        "keywords": ["engine room", "boiler", "main engine", "diesel engine", "bedplate",
                     "crankcase", "cylinder head", "auxiliary", "purifier", "compressor",
                     "refrigeration", "topmost part", "bottom most"],
        "concepts": {
            "Engine Room Spaces": ["engine room", "within the engine room", "e/r"],
            "Main & Auxiliary Machinery": ["main engine", "boiler", "auxiliary", "generator", "compressor"],
            "Engine Structure": ["bedplate", "crankcase", "cylinder head", "topmost", "bottom most"],
        },
    },
    "Hand Tools & Fasteners": {
        "keywords": ["bolt", "stud", "nut", "tap", "die", "spanner", "thread", "vice",
                     "hammer", "chisel", "file", "drill", "hacksaw", "screwdriver", "plier"],
        "concepts": {
            "Fasteners": ["bolt", "stud", "nut", "washer", "thread"],
            "Thread Cutting": ["tap", "die", "internal thread", "external thread"],
            "Hand Tools": ["spanner", "vice", "hammer", "chisel", "file", "hacksaw", "plier"],
        },
    },
    "Diesel Engine Systems": {
        "keywords": ["diesel engine", "cylinder head", "turbocharger", "turning gear",
                     "exhaust gas economiser", "fresh water", "cooling", "scavenge",
                     "fuel injector", "piston", "crankshaft", "camshaft", "starting air"],
        "concepts": {
            "Engine Components": ["cylinder head", "piston", "crankshaft", "camshaft", "injector"],
            "Cooling & Lubrication": ["fresh water", "cooling", "lubricating oil", "circulation"],
            "Air & Exhaust": ["turbocharger", "scavenge", "exhaust gas economiser", "starting air"],
            "Turning Gear": ["turning gear", "barring"],
        },
    },
    "Machine Tools & Workshop Practice": {
        "keywords": ["lathe", "drilling machine", "grinding", "shaping", "milling",
                     "machine tool", "flange", "axial hole", "round bar", "turning",
                     "chuck", "tail stock", "cutting tool"],
        "concepts": {
            "Lathe Work": ["lathe", "turning", "chuck", "tail stock", "round bar"],
            "Drilling & Grinding": ["drilling", "grinding", "axial hole", "holes in a plate"],
            "Tool Selection": ["machine tool", "what machine", "will you be using"],
        },
    },
    "Welding & Cutting": {
        "keywords": ["welding", "arc welding", "gas welding", "electrode", "oxygen",
                     "acetylene", "cutting", "gouging", "weld", "flux", "slag", "spatter"],
        "concepts": {
            "Arc Welding": ["arc welding", "electrode", "angle", "flux", "slag"],
            "Gas Welding & Cutting": ["gas welding", "oxygen", "acetylene", "cutting torch"],
            "Welding Safety": ["before starting arc welding", "protection", "welding screen"],
        },
    },
    "Level Measurement & Sounding": {
        "keywords": ["gauge glass", "level indicator", "sounding tape", "dip stick",
                     "sounding", "level measuring", "remote level indicator", "ullage",
                     "tank level", "sight glass"],
        "concepts": {
            "Sounding Devices": ["sounding tape", "dip stick", "sounding pipe", "ullage"],
            "Gauge Glasses": ["gauge glass", "sight glass", "level indicator"],
            "Remote Indication": ["remote level indicator", "tank gauging"],
        },
    },
    "Insulation & Lagging": {
        "keywords": ["insulation", "lagging", "glass wool", "asbestos", "heat transfer",
                     "insulating material", "thermal", "cladding"],
        "concepts": {
            "Insulating Materials": ["glass wool", "asbestos", "insulating material", "banned"],
            "Lagging Practice": ["lagging", "wrapped around", "pipes", "boilers"],
            "Handling Safety": ["working with insulating", "protect your body"],
        },
    },
    "Chemical Handling & Safety": {
        "keywords": ["chemical", "msds", "chemical container", "spill", "disposal",
                     "stored", "protective", "corrosive", "solvent", "acid"],
        "concepts": {
            "Storage": ["stored in", "chemical container", "chemical locker"],
            "Spill Response": ["fall on the body", "first action", "spill", "wash"],
            "Disposal": ["disposal", "used/expired", "landed ashore"],
        },
    },
    "Steering Gear & Thrusters": {
        "keywords": ["steering gear", "rudder", "thruster", "bow thruster", "stern thruster",
                     "tiller", "rudder stock", "steering flat", "hydraulic", "telemotor"],
        "concepts": {
            "Steering Gear": ["steering gear", "rudder stock", "tiller", "telemotor", "steering flat"],
            "Rudder": ["rudder", "turn the", "helm"],
            "Thrusters": ["thruster", "bow thruster", "stern thruster"],
        },
    },
    "Tanks, Valves & Ballast Systems": {
        "keywords": ["quick closing valve", "man hole", "air vent", "sounding pipe",
                     "ballast tank", "double bottom", "tank", "valve", "non return valve",
                     "cock", "bilge"],
        "concepts": {
            "Quick Closing Valves": ["quick closing valve", "remotely closed", "emergency"],
            "Tank Fittings": ["man hole", "air vent", "sounding pipe", "vent"],
            "Ballast & Bilge": ["ballast tank", "bilge", "double bottom", "filled up with"],
        },
    },
    "Engine Room Alarms & Emergency Response": {
        "keywords": ["alarm", "co2 alarm", "fire alarm", "general alarm", "ums",
                     "machinery failure", "injured person", "first action", "dead man alarm",
                     "emergency stop"],
        "concepts": {
            "Alarm Types": ["fire alarm", "co2 alarm", "general alarm", "machinery failure", "ums"],
            "Emergency Response": ["first action", "injured person", "on hearing", "evacuate"],
        },
    },
    "Fire Fighting Equipment": {
        "keywords": ["fire", "fire triangle", "extinguisher", "co2", "foam", "dry powder",
                     "fixed fire fighting", "fire main", "hydrant", "nozzle", "fire pump",
                     "sprinkler", "emergency fire pump"],
        "concepts": {
            "Fire Theory": ["fire triangle", "class of fire", "combustion"],
            "Portable Extinguishers": ["extinguisher", "co2", "foam", "dry powder"],
            "Fixed Systems": ["fixed fire fighting", "sprinkler", "fire main", "hydrant", "fire pump"],
        },
    },
    "Basic Electrical Safety": {
        "keywords": ["insulation testing", "megger", "shock", "electrical", "earth",
                     "lockout", "isolate", "resistance", "fatal current", "live",
                     "circuit breaker", "fuse"],
        "concepts": {
            "Insulation Testing": ["insulation testing", "megger", "resistance", "ohms"],
            "Electric Shock": ["shock current", "fatal", "body resistance", "live"],
            "Safe Isolation": ["before starting maintenance", "re-starting a machine",
                               "lockout", "isolate", "precautions"],
        },
    },
}
