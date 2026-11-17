"""
generator/v030/job_catalogue.py

Constructs the 28-row base intervention job catalogue for Cairn Oil & Gas — Barmer Basin
conforming to spec/02_data_contract.md §7 and decision_architecture.md §3.1.
Enforces TC-008.6: 8 rigless jobs in the base 28 rows (plus rigless GLV_REPLACE in catalogue.py).
"""

import pandas as pd


def generate_job_catalogue() -> pd.DataFrame:
    jobs = [
        # WAX
        ("WAX_SCRAPE", "Mechanical paraffin scraping (slickline/pulling)", "WAX", "WAX",
         "THP rise, WHT drop near 42C pour point, gradual liquid drop, waxy crude history", True, "PULLING_UNIT", 1.5, 12.0),
        ("WAX_HOTOIL", "Hot oil / hot water thermal wash (HOCU >65C)", "WAX", "WAX",
         "THP rise, flowline WHT drop below 58C WAT, gradual liquid decline", False, "HOT_OILER", 0.5, 3.5),
        ("WAX_SOLVENT", "Aromatic solvent / xylene-dispersant soak", "WAX", "WAX",
         "Paraffin/asphaltene recurrence despite hot-oil circulation", False, "PUMP_TRUCK", 1.5, 6.0),
        ("WAX_INHIBITOR", "Continuous pour-point depressant / wax inhibitor squeeze", "WAX", "WAX",
         ">=3 wax deposition events in 12 months on high-WAT pad", False, "PUMP_TRUCK", 1.5, 8.0),
        ("WAX_HEATER", "Skin-effect trace-heater & downhole thermal system overhaul", "WAX", "WAX",
         "Flowline/tubing heater controller degradation, WHT <43C pour point, high PCP/ESP torque", True, "WORKOVER_RIG", 2.5, 25.0),

        # MECHANICAL
        ("ROD_REPLACE", "Drive-rod string / PCP rod / ESP power-cable remediation", "MECHANICAL", "ROD_PART",
         "Sudden rate collapse or electrical/torque trip, CHP unchanged", True, "PULLING_UNIT", 1.5, 14.0),
        ("PUMP_OVERHAUL", "Artificial lift pump overhaul (ESP wet-end / PCP stator-rotor / SRP insert)", "MECHANICAL", "PUMP_WEAR",
         "Gradual liquid decline + CHP/intake pressure rise, lift efficiency divergence", True, "PULLING_UNIT", 2.0, 18.0),
        ("TUBING_REPLACE", "Production tubing string replacement / descaling (3-1/2\" / 2-7/8\")", "MECHANICAL", "TUBING_LEAK",
         "Sharp rate drop over 3-5d, pressure communication, displacement gap", True, "WORKOVER_RIG", 3.5, 30.0),
        ("SURFACE_REPAIR", "Wellhead, pad manifold & heated flowline equipment repair", "MECHANICAL", "SURFACE",
         "Runtime hours collapse with no downhole signature", False, "SURFACE_CREW", 0.5, 2.0),
        ("LIFT_OPTIM", "Lift optimisation (VSD Hz / Jet-Pump power-fluid / PCP RPM / SRP stroke)", "MECHANICAL", "SURFACE",
         "Sub-optimal submergence or fillage proxy divergence without mechanical damage", False, "SURFACE_CREW", 0.5, 1.5),
        ("GAS_SEP_INSTALL", "Rotary gas separator / intake shroud installation & PSD reset", "MECHANICAL", "SURFACE",
         "Lift efficiency loss with free-gas interference or GOR rise", True, "PULLING_UNIT", 3.0, 20.0),
        ("LIFT_CONVERSION", "Artificial lift conversion (ESP <-> Hydraulic Jet Pump / PCP resize)", "MECHANICAL", "OTHER",
         "Repeated polymer/solids pump fouling or rate mismatch across >=2 cycles", True, "WORKOVER_RIG", 3.5, 45.0),

        # DEPOSITION & FILL
        ("SCALE_ACID_BULLHEAD", "Inorganic & polymer-carbonate scale removal (inhibited HCl bullhead)", "DEPOSITION", "SCALE",
         "Flat production then intake restriction, elevated carbonate/polymer scaling index", False, "PUMP_TRUCK", 1.5, 8.5),
        ("SCALE_INHIBITOR", "Phosphonate / polymeric scale inhibitor squeeze", "DEPOSITION", "SCALE",
         "Scale recurrence in polymer-flood producer, scaling index persistently > 0", False, "PUMP_TRUCK", 1.5, 7.0),
        ("SAND_CLEANOUT", "Coiled-tubing / bailer sand & proppant cleanout", "DEPOSITION", "SAND",
         "Gradual decline, Fatehgarh sand or Barmer Hill proppant solids in fluid, tagged fill", True, "PULLING_UNIT", 2.5, 16.0),
        ("SAND_CONTROL", "Standalone / expandable sand-control screens & resin consolidation", "DEPOSITION", "SAND",
         "Repeated sand cleanouts + accelerated Jet-Pump nozzle or ESP stage wear", True, "WORKOVER_RIG", 7.0, 65.0),

        # INFLOW RESTORATION
        ("RE_PERFORATION", "High-shot-density re-perforation of Fatehgarh / Barmer Hill pay", "INFLOW", "OTHER",
         "PI decline with static reservoir pressure intact across stacked channel sands", True, "WORKOVER_RIG", 3.0, 28.0),
        ("ADD_PERFORATION", "Add-perforation into bypassed Fatehgarh FM1-FM3 channel lobes", "INFLOW", "OTHER",
         "Log-derived bypassed fluvial pay in current zone", True, "WORKOVER_RIG", 3.0, 32.0),
        ("MATRIX_ACID", "Matrix acidising & near-wellbore polymer-skin cleanup", "INFLOW", "OTHER",
         "PI decline, formation damage skin, clean perforations with no fill", True, "WORKOVER_RIG", 2.0, 22.0),
        ("HYDRAULIC_FRAC", "Multi-stage proppant hydraulic fracturing / re-frac (Barmer Hill & RDG Volcanics)", "INFLOW", "OTHER",
         "Low inflow in tight porcellanite or volcanic reservoir with intact wellhead/casing barriers", True, "WORKOVER_RIG", 5.5, 95.0),
        ("ZONE_TRANSFER", "Up-hole Fatehgarh zone transfer / behind-casing pay recompletion", "INFLOW", "OTHER",
         "Lower FM4/FM5 watered out (>90% WC) + upper FM1/FM2 pay confirmed on logs", True, "WORKOVER_RIG", 7.5, 70.0),

        # WATER & POLYMER CONFORMANCE CONTROL
        ("CHOKE_BACK", "Conformance choke back / drawdown management", "WATER_CONTROL", "OTHER",
         "WOR derivative negative coning slope or condensate banking control", False, "SURFACE_CREW", 0.5, 1.0),
        ("CEMENT_SQUEEZE", "Remedial cement squeeze + selective re-perforation", "WATER_CONTROL", "OTHER",
         "WOR derivative positive channelling slope + poor CBL bond across shale break", True, "WORKOVER_RIG", 6.5, 55.0),
        ("STRADDLE_PACKER", "Selective zonal isolation / straddle packer assembly", "WATER_CONTROL", "OTHER",
         "High-perm watered-out thief layer isolated between mechanical packers", True, "WORKOVER_RIG", 4.5, 40.0),
        ("POLYMER_GEL", "Crosslinked HPAM polymer-gel conformance treatment (RPM shut-off)", "WATER_CONTROL", "OTHER",
         "HPAM polymer breakthrough + WOR positive channelling slope in EOR pattern", True, "WORKOVER_RIG", 4.0, 60.0),
        ("CASING_REPAIR", "Casing patch / barrier integrity repair & cement squeeze", "WATER_CONTROL", "OTHER",
         "Failed annular pressure test or casing leak requiring barrier restoration prior to frac/production", True, "WORKOVER_RIG", 7.0, 65.0),

        # TERMINAL
        ("NO_JOB_JUSTIFIED", "NO JOB JUSTIFIED (Sub-economic / reservoir depletion)", "TERMINAL", "OTHER",
         "Decline fit clean, no mechanical/conformance remedy economic, offsets declining identically", False, "SURFACE_CREW", 0.0, 0.0),
        ("PLUG_ABANDON", "Permanent plug and abandon (P&A)", "TERMINAL", "OTHER",
         "Rate < opex limit, watered-out flank (>95% WC), zero behind-casing opportunity", True, "WORKOVER_RIG", 6.0, 45.0),
    ]

    columns = [
        "job_code", "job_name", "category", "mechanism_code",
        "selection_evidence", "requires_rig", "equipment", "est_days", "est_cost_lakh_inr"
    ]
    df = pd.DataFrame(jobs, columns=columns)
    return df


if __name__ == "__main__":
    df = generate_job_catalogue()
    print(f"Total jobs: {len(df)}")
    print(f"Rig jobs: {(df['requires_rig'] == True).sum()}, Rigless jobs: {(df['requires_rig'] == False).sum()}")
    print("Rigless jobs:\n", df[df['requires_rig'] == False][['job_code', 'job_name', 'equipment']])
