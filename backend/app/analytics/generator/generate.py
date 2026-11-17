"""Cairn Oil & Gas — Barmer Basin 60-month synthetic data generator (Stage C1; docs/build.md).

    uv run python -m app.analytics.generator.generate --field all --start 2021-10-01 --end 2026-09-30

Writes parquet to ``settings.LANDING_DIR`` (or ``--out``):
    <out>/<field_lower>/<table>.parquet   well-keyed tables per field (Mangala, Bhagyam, Aishwariya, Raageshwari)
    <out>/asset/<table>.parquet           job_catalogue, mro_inventory, rig_calendar, field_master,
                                          cluster_master, facility_master, field_targets

All 4 Barmer fields (460 wells total) are simulated natively over 2021-10-01 → 2026-09-30.
Fully deterministic: no wall-clock reads; every random draw is seeded; two runs produce byte-identical parquet (V-N3).
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from app import settings
from app.analytics.generator.v030.supporting import (
    generate_decision_log,
    generate_draft_plan_table,
    generate_mro_inventory,
    generate_rig_calendar,
    generate_well_run,
)

from .catalogue import build_job_catalogue
from .construction import (
    generate_casing_tally,
    generate_perforation_intervals,
    generate_tubing_string,
)
from .fields import FIELD_CONFIGS, resolve_field
from .fields.base import FieldConfig
from .formation_tops import generate_formation_tops
from .hierarchy import cluster_master, facility_master, field_master
from .native import native_tables, run_native_field
from .operations_events import assemble
from .pressure_surveys import generate_pressure_surveys
from .targets import build_field_targets

LINEAGE_AT = "2026-09-23T16:00:00Z"
LINEAGE_COLS = ["_ingested_at", "_source_system", "_source_file", "_batch_id"]


def v04_lineage(df: pd.DataFrame, table: str, batch: str, folder: str) -> pd.DataFrame:
    df = df.copy()
    df["_ingested_at"] = LINEAGE_AT
    df["_source_system"] = "GENERATOR"
    df["_source_file"] = f"gs://urvi-cairn-barmer-ai-agent-datalake/bronze/{folder}/{table}.parquet"
    df["_batch_id"] = batch
    return df


def construction_tables(
    cfg: FieldConfig,
    wells: pd.DataFrame,
    wo: pd.DataFrame,
    daily: pd.DataFrame,
    start: date,
    end: date,
) -> dict[str, pd.DataFrame]:
    s = cfg.seed * 100
    done = wo[wo["outcome"] != "IN_PROGRESS"]
    wo_c = done[["workover_id", "well_id", "start_date", "end_date", "catalogue_job_code", "is_censored"]]
    d_c = daily[["well_id", "production_date", "liquid_rate_blpd", "is_producing"]]
    return dict(
        casing_tally=generate_casing_tally(wells, s + 31),
        tubing_string=generate_tubing_string(wells, wo_c, s + 32),
        perforation_intervals=generate_perforation_intervals(wells, wo_c, s + 33),
        formation_tops=generate_formation_tops(wells, s + 34),
        pressure_surveys=generate_pressure_surveys(wells, d_c, start, end, s + 35),
    )


def build_native(cfg: FieldConfig, start: date) -> tuple[dict[str, pd.DataFrame], pd.Series, set]:
    run = run_native_field(cfg, settings.AS_OF)
    tb = dict(native_tables(cfg, run))
    batch, fold = f"BATCH-{cfg.field.upper()}-V04", cfg.field.lower()
    ev = assemble([pd.DataFrame(run["res"].events)], cfg.field)
    tb["operations_events"] = ev
    tb.update(
        construction_tables(
            cfg,
            tb["well_master"],
            tb["workover_history"],
            tb["daily_production"],
            cfg.start,
            cfg.end,
        )
    )
    if cfg.field == "Mangala":
        well_run = generate_well_run(tb["well_master"], tb["daily_production"], run_date=settings.AS_OF)
        tb["well_run"] = well_run
        tb["draft_plan"] = generate_draft_plan_table(well_run)
        tb["decision_log"] = generate_decision_log()
    tables = {k: v04_lineage(v, k, batch, fold) for k, v in tb.items()}
    pot = pd.Series(np.sum(list(run["res"].potential.values()), axis=0), index=pd.date_range(cfg.start, cfg.end))
    idle = set(tb["well_master"].loc[tb["well_master"]["status"] == "IDLE", "well_id"])
    return tables, pot, idle


STRING_NULL_COLS = {"rod_string_grade", "pump_type"}


def write_tables(out: Path, folder: str, tables: dict[str, pd.DataFrame]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    d = out / folder
    d.mkdir(parents=True, exist_ok=True)
    for name in sorted(tables):
        t = pa.Table.from_pandas(tables[name], preserve_index=False)
        cols, fields = [], []
        for f, col in zip(t.schema, t.columns):
            if f.type == pa.null():
                target_type = pa.string() if f.name in STRING_NULL_COLS else pa.float64()
                col = col.cast(target_type)
                f = pa.field(f.name, target_type)
            cols.append(col)
            fields.append(f)
        pq.write_table(pa.Table.from_arrays(cols, schema=pa.schema(fields)), d / f"{name}.parquet")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--field", default="all")
    ap.add_argument("--start", default=str(settings.DATA_START))
    ap.add_argument("--end", default=str(settings.DATA_END))
    ap.add_argument("--out", default=str(settings.LANDING_DIR))
    a = ap.parse_args(argv)
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)
    if (start, end) != (settings.DATA_START, settings.DATA_END):
        print(
            f"ERROR: the v0.4 window is fixed at {settings.DATA_START}..{settings.DATA_END} (D-2, V-N5)",
            file=sys.stderr,
        )
        return 2
    if a.field.lower() == "all":
        fields = list(FIELD_CONFIGS)
    else:
        f = resolve_field(a.field)
        if f is None:
            print(f"ERROR: unknown field {a.field}", file=sys.stderr)
            return 2
        fields = [f]
    out = Path(a.out)
    wells_by_field, targets = {}, []
    for f in fields:
        cfg = FIELD_CONFIGS[f]
        tables, pot, idle = build_native(cfg, start)
        write_tables(out, f.lower(), tables)
        wells_by_field[f] = tables["well_master"]
        targets.append(build_field_targets(f, pot, tables["daily_production"], idle))
        print(f"{f}: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(tables.items())))
    if a.field.lower() == "all":
        cfgs = [FIELD_CONFIGS[f] for f in fields]
        cat = v04_lineage(build_job_catalogue(), "job_catalogue", "BATCH-ASSET-V04", "asset")
        asset = dict(
            job_catalogue=cat,
            mro_inventory=v04_lineage(generate_mro_inventory(), "mro_inventory", "BATCH-ASSET-V04", "asset"),
            rig_calendar=v04_lineage(generate_rig_calendar(), "rig_calendar", "BATCH-ASSET-V04", "asset"),
            field_master=v04_lineage(field_master(cfgs, wells_by_field), "field_master", "BATCH-ASSET-V04", "asset"),
            cluster_master=v04_lineage(cluster_master(cfgs, wells_by_field), "cluster_master", "BATCH-ASSET-V04", "asset"),
            facility_master=v04_lineage(facility_master(cfgs), "facility_master", "BATCH-ASSET-V04", "asset"),
            field_targets=v04_lineage(pd.concat(targets, ignore_index=True), "field_targets", "BATCH-ASSET-V04", "asset"),
        )
        write_tables(out, "asset", asset)
        print("asset: " + ", ".join(f"{k}={len(v)}" for k, v in sorted(asset.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
