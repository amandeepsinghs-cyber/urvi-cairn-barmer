"""FieldConfig dataclasses for Cairn Oil & Gas — Barmer Basin (RJ-ON-90/1).

Each Barmer field (Mangala, Bhagyam, Aishwariya, Raageshwari) is described by one frozen
``FieldConfig`` calibrated to public SPE / DGH / Cairn-Vedanta engineering bounds in
``docs/build.md`` Part I.

All numbers in the field modules are orchestrator-reviewed design parameters (DELEGATION.md).
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field as dc_field
from datetime import date


@dataclass(frozen=True)
class ClusterConfig:
    cluster_id: str
    cluster_type: str                 # WELL_PAD | GGS | FAULT_BLOCK
    center: tuple[float, float]       # (lat, lon), synthetic Barmer Basin coordinates
    weight: float                     # share of the field's wells
    spread_deg: float = 0.010         # 1-sigma scatter of well positions around the pad centre


@dataclass(frozen=True)
class FacilityConfig:
    facility_id: str
    facility_type: str                # GGS (Pad Manifold) | CDP (Central Terminal: MPT, CPF, RGT)
    name: str
    lat: float
    lon: float
    capacity_bopd: int
    serviced_cluster_ids: tuple[str, ...]
    compressor_capacity_mmscfd: float | None = None
    water_handling_bwpd: int | None = None


@dataclass(frozen=True)
class FixtureSpec:
    """A scripted Barmer demo story (docs/build.md Part I §7). ``kind`` selects ``generator.fixtures``."""

    well_id: str
    kind: str
    lift_type: str
    cluster_id: str | None = None
    zone: str | None = None
    params: dict = dc_field(default_factory=dict)


@dataclass(frozen=True)
class ReservoirRanges:
    """Uniform ranges for per-well production parameters (native 60-month simulation)."""

    q_i_bopd: tuple[float, float]
    b: tuple[float, float]
    d_i_per_yr: tuple[float, float]
    wc_init_pct: tuple[float, float]
    wc_slope_pp_per_yr: tuple[float, float]
    thp_kgcm2: tuple[float, float]
    chp_kgcm2: tuple[float, float]
    gor_scf_bbl: tuple[float, float]
    wht_degc: tuple[float, float]
    gl_inj_rate_mscfd: tuple[float, float]
    gl_inj_pressure_kgcm2: tuple[float, float]


@dataclass(frozen=True)
class DowntimeModel:
    """Renewal-process and desert workover logistics parameters (native simulation)."""

    uptime_weibull_k: float
    uptime_scale_days: float
    rig_wait_median_days_start: float     # median WAIT_ON_RIG at the window start
    rig_wait_median_days_end: float       # ... and at the window end (linear drift; Bhagyam deteriorates)
    rig_wait_sigma: float                 # lognormal sigma
    p_wait_on_material: float
    material_wait_median_days: float
    p_permit_delay: float
    p_crew_unavailable: float
    p_deferred_maintenance: float         # degraded running beyond SLA before a rigless job
    outcome_p: tuple[float, float, float]  # SUCCESS / PARTIAL / FAILED
    uptime_scale_days_end: float | None = None


@dataclass(frozen=True)
class FieldConfig:
    field: str
    prefix: str
    n_wells: int
    seed: int
    asset: str
    centroid: tuple[float, float]                  # synthetic Barmer Basin coordinates
    clusters: tuple[ClusterConfig, ...]
    facilities: tuple[FacilityConfig, ...]
    zones: dict[str, float]                        # Fatehgarh_Lower / Fatehgarh_Upper / Barmer_Hill / Raageshwari_Volcanics
    lift_mix: dict[str, float]                     # ESP / JET_PUMP / PCP / SRP / GAS_LIFT / NATURAL
    mechanism_weights: dict[str, dict[str, float]]  # lift_type -> catalogue job_code -> weight
    ops_event_rates: dict[str, float]              # per well-year or cluster-year by event_type
    target_bias: float                             # designed field gap vs target (F-09), fraction
    fixtures: dict[str, FixtureSpec]
    reservoir: ReservoirRanges | None = None
    downtime: DowntimeModel | None = None
    primary_reservoirs: tuple[str, ...] = (
        "Fatehgarh_Lower",
        "Fatehgarh_Upper",
        "Barmer_Hill",
        "Raageshwari_Volcanics",
    )
    completion_window: tuple[date, date] = (date(2008, 6, 1), date(2021, 6, 30))
    spud_lead_days: tuple[int, int] = (25, 65)
    surface_elevation_m: tuple[float, float] = (150.0, 180.0)
    surface_shoe_m: tuple[float, float] = (220.0, 380.0)
    casing_mix_in: dict[float, float] = dc_field(default_factory=lambda: {7.0: 0.70, 9.625: 0.30})
    tubing_mix_in: dict[float, float] = dc_field(default_factory=lambda: {3.5: 0.85, 2.875: 0.15})
    zone_depths_md: dict[str, tuple[float, float, float, float]] = dc_field(default_factory=dict)
    zone_md_tvd_ratio: dict[str, tuple[float, float]] = dc_field(default_factory=dict)
    idle_fraction: float = 0.045
    boundary_radius_deg: float = 0.06
    fluid_props: dict = dc_field(default_factory=dict)
    start: date = date(2021, 10, 1)
    end: date = date(2026, 9, 30)
    native: bool = True
