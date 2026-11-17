"""Unit tests for Stage N data generator validator and data contracts."""

from __future__ import annotations

import shutil
from datetime import timedelta
from pathlib import Path

import pandas as pd
import pytest

from app import settings
from app.analytics.generator import validate

BASELINE_DIR = Path(__file__).resolve().parent.parent / "baseline" / "landing_v030"


@pytest.fixture(scope="module")
def landing() -> Path:
    """Return landing path if data is generated, else skip."""
    landing_dir = settings.LANDING_DIR
    if not (landing_dir / "asset" / "field_targets.parquet").exists():
        pytest.skip("landing data not generated; run app.analytics.generator.generate")
    return landing_dir


@pytest.fixture(scope="module")
def mutable_landing(tmp_path_factory: pytest.TempPathFactory, landing: Path) -> Path:
    """Provide a module-level mutable copy of the landing data directory."""
    temp_dir = tmp_path_factory.mktemp("mutable_landing") / "landing"
    shutil.copytree(landing, temp_dir)
    return temp_dir


def _make_field_test_copy(tmp_path: Path, mutable_landing: Path, field: str = "aishwariya") -> Path:
    """Create a minimal per-test landing copy containing asset/ and the field folder."""
    target_landing = tmp_path / "landing"
    target_landing.mkdir(parents=True, exist_ok=True)
    shutil.copytree(mutable_landing / "asset", target_landing / "asset")
    shutil.copytree(mutable_landing / field, target_landing / field)
    return target_landing


def test_validator_clean_on_generated_data(landing: Path) -> None:
    assert validate.main(["--field", "all", "--landing", str(landing)]) == 0


def test_well_counts(landing: Path) -> None:
    expected = {
        "mangala": (180, "MNG-", 4),
        "bhagyam": (120, "BHG-", 3),
        "aishwariya": (100, "ASH-", 3),
        "raageshwari": (60, "RAG-", 3),
    }
    for field_name, (count, prefix, clusters) in expected.items():
        wm = pd.read_parquet(landing / field_name / "well_master.parquet")
        assert len(wm) == count, f"{field_name}: expected {count} wells, found {len(wm)}"
        assert wm["well_id"].str.startswith(prefix).all(), f"{field_name}: not all wells start with {prefix}"
        if clusters is not None:
            assert wm["cluster_id"].nunique() == clusters, (
                f"{field_name}: expected {clusters} clusters, found {wm['cluster_id'].nunique()}"
            )


def test_ic_counts_min_30(landing: Path) -> None:
    counts = validate.ic_counts(landing)
    for i in range(1, 16):
        ic = f"IC-{i:02d}"
        assert ic in counts, f"{ic} missing from ic_counts"
        assert counts[ic] >= 30, f"{ic} count {counts[ic]} < 30"


def test_bhg019_waits(landing: Path) -> None:
    fn = getattr(validate, "bhg019_waits", getattr(validate, "lkw047_waits"))
    waits = fn(landing)
    assert waits["wait_on_rig_days"] == 38
    assert waits["wait_on_material_days"] == 11


def test_bhagyam_gap(landing: Path) -> None:
    gap_val = validate.gap(landing, "Bhagyam", validate.QTD)
    assert -0.19 <= gap_val <= -0.13, f"Bhagyam QTD gap {gap_val:.3f} outside [-0.19, -0.13]"


def test_rag014_offsets(landing: Path) -> None:
    fn = getattr(validate, "rag014_residuals", getattr(validate, "lkm090_residuals"))
    residuals = fn(landing)
    assert residuals["max_abs_residual_pp"] <= 5.0
    assert len(residuals["offsets"]) >= 4


def test_no_currency_columns(landing: Path) -> None:
    currency_tokens = ("usd", "currency", "payback")
    for field in ("mangala", "bhagyam", "aishwariya", "raageshwari"):
        for path in (landing / field).glob("*.parquet"):
            df = pd.read_parquet(path)
            for col in df.columns:
                col_lower = col.lower()
                assert not any(tok in col_lower for tok in currency_tokens), (
                    f"Found currency token in {path.name}:{col}"
                )


def test_no_wall_clock_in_generator() -> None:
    assert validate.check_no_wall_clock() == []


def test_detects_dc014(tmp_path: Path, mutable_landing: Path) -> None:
    target = _make_field_test_copy(tmp_path, mutable_landing, "aishwariya")
    dp_path = target / "aishwariya" / "daily_production.parquet"
    df = pd.read_parquet(dp_path)
    mask = ~df["is_producing"].astype(bool)
    idx = df[mask].index[:5]
    df.loc[idx, "oil_rate_bopd"] = 0.0
    df.to_parquet(dp_path, index=False)
    violations = validate.check_field(target, "Aishwariya")
    assert any(v.startswith("DC-014") for v in violations), f"Expected DC-014 violation, got: {violations}"


def test_detects_gl_on_srp(tmp_path: Path, mutable_landing: Path) -> None:
    target = _make_field_test_copy(tmp_path, mutable_landing, "aishwariya")
    wm = pd.read_parquet(target / "aishwariya" / "well_master.parquet")
    srp_wells = wm[wm["lift_type"] == "SRP"]["well_id"].tolist()
    dp_path = target / "aishwariya" / "daily_production.parquet"
    df = pd.read_parquet(dp_path)
    mask = df["well_id"].isin(srp_wells) & df["is_producing"].astype(bool)
    idx = df[mask].index[:3]
    df.loc[idx, "gl_inj_rate_mscfd"] = 300.0
    df.to_parquet(dp_path, index=False)
    violations = validate.check_field(target, "Aishwariya")
    assert any(v.startswith("V-N7") for v in violations), f"Expected V-N7 violation, got: {violations}"


def test_detects_bad_event_window(tmp_path: Path, mutable_landing: Path) -> None:
    target = _make_field_test_copy(tmp_path, mutable_landing, "aishwariya")
    ev_path = target / "aishwariya" / "operations_events.parquet"
    dp_path = target / "aishwariya" / "daily_production.parquet"
    ev = pd.read_parquet(ev_path)
    dp = pd.read_parquet(dp_path)

    target_well = ev.iloc[0]["well_id"]
    w_dp = dp[dp["well_id"] == target_well].sort_values("production_date").reset_index(drop=True)

    found = False
    for i in range(len(w_dp) - 2):
        row0, row1, row2 = w_dp.iloc[i], w_dp.iloc[i + 1], w_dp.iloc[i + 2]
        if (
            row1["production_date"] == row0["production_date"] + timedelta(days=1)
            and row2["production_date"] == row0["production_date"] + timedelta(days=2)
            and row0["is_producing"]
            and row0["runtime_fraction"] >= 0.999
            and row1["is_producing"]
            and row1["runtime_fraction"] >= 0.999
            and row2["is_producing"]
            and row2["runtime_fraction"] >= 0.999
        ):
            ev.loc[0, "start_date"] = row0["production_date"]
            ev.loc[0, "end_date"] = row2["production_date"]
            found = True
            break

    assert found, "Could not find 3 consecutive fully-producing days"
    ev.to_parquet(ev_path, index=False)
    violations = validate.check_field(target, "Aishwariya")
    assert any(v.startswith("V-N2") for v in violations), f"Expected V-N2 violation, got: {violations}"


def test_detects_wrong_well_count(tmp_path: Path, mutable_landing: Path) -> None:
    target = _make_field_test_copy(tmp_path, mutable_landing, "aishwariya")
    wm_path = target / "aishwariya" / "well_master.parquet"
    wm = pd.read_parquet(wm_path)
    wm = wm.iloc[:-1]
    wm.to_parquet(wm_path, index=False)
    violations = validate.check_field(target, "Aishwariya")
    assert any(v.startswith("V-N1") for v in violations), f"Expected V-N1 violation, got: {violations}"
