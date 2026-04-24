#!/usr/bin/env python3
"""Validation script for materials paper extraction output.

Checks extraction JSON against the schema defined in 03-extract-system-prompt.md.
Separates hard errors (schema violations) from soft warnings (suspicious values).

The output file is written even when errors are present, so downstream steps
(review, revise) can still run and catch the issues. Callers that want to halt
on errors should check the exit code.

Exit codes:
  0 — validation passed (may include warnings)
  1 — validation failed with hard errors
  2 — I/O or usage error
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from typing import Any

logger = logging.getLogger("validate")

# Canonical matrix-phase tokens that are always acceptable as Main_Phase.
ALLOWED_MAIN_PHASE_TOKENS: frozenset[str] = frozenset(
    {
        "gamma", "γ", "fcc", "bcc", "hcp",
        "austenite", "martensite", "ferrite", "pearlite", "bainite",
        "alpha", "α", "beta", "β", "delta", "δ",
        "matrix",
    }
)

# Secondary-phase tokens that must not dominate Main_Phase.
FORBIDDEN_MAIN_PHASE_TOKENS: frozenset[str] = frozenset(
    {
        "laves", "sigma", "mu",
        "mc", "m2c", "m6c", "m7c3", "m23c6", "m₂c", "m₆c", "m₇c₃", "m₂₃c₆",
        "carbide", "nitride", "boride",
    }
)

_WORD_RE = re.compile(r"[a-z0-9₀-₉α-ωγδ]+")


def _tokenize_phase(phase: str) -> list[str]:
    """Lowercase tokenize a Main_Phase string for whole-word matching."""
    return _WORD_RE.findall(phase.lower())


def _main_phase_violation(phase: str) -> str | None:
    """Return the offending token if the phase is dominated by a secondary phase.

    Heuristic: if any allowed matrix token is present, accept the phase.
    Otherwise flag the first forbidden token found.
    """
    tokens = set(_tokenize_phase(phase))
    if tokens & ALLOWED_MAIN_PHASE_TOKENS:
        return None
    for token in tokens:
        if token in FORBIDDEN_MAIN_PHASE_TOKENS:
            return token
    return None


def validate(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Validate extraction JSON. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    _validate_paper_metadata(data.get("Paper_Metadata"), errors)

    if "items" not in data:
        errors.append("Missing root items[]")
        return errors, warnings

    items = data.get("items")
    if not isinstance(items, list):
        errors.append(f"items must be list, got {type(items).__name__}")
        return errors, warnings
    if not items:
        errors.append("items[] is empty")
        return errors, warnings

    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errors.append(f"Item {i}: must be dict, got {type(item).__name__}")
            continue
        _validate_item(i, item, errors, warnings)

    return errors, warnings


def _validate_paper_metadata(pm: Any, errors: list[str]) -> None:
    if pm is None:
        errors.append("Missing root Paper_Metadata")
        return
    if not isinstance(pm, dict):
        errors.append(f"Paper_Metadata must be dict, got {type(pm).__name__}")
        return
    title = pm.get("Paper_Title")
    if title is not None and not isinstance(title, str):
        errors.append(
            f"Paper_Metadata.Paper_Title must be str or null, got {type(title).__name__}"
        )
    doi = pm.get("DOI")
    if doi is not None and not isinstance(doi, str):
        errors.append(
            f"Paper_Metadata.DOI must be str or null, got {type(doi).__name__}"
        )


def _validate_item(
    i: int, item: dict[str, Any], errors: list[str], warnings: list[str]
) -> None:
    # Sample_ID is required and must be a non-empty string.
    sid = item.get("Sample_ID")
    if not sid or not isinstance(sid, str):
        errors.append(f"Item {i}: Sample_ID must be a non-empty string, got {sid!r}")

    for req in ("Composition_Info", "Process_Info", "Microstructure_Info", "Properties_Info"):
        if req not in item:
            errors.append(f"Item {i}: missing {req}")

    gm = item.get("Gradient_Material")
    if gm is not None and not isinstance(gm, bool):
        errors.append(
            f"Item {i}: Gradient_Material must be bool, got {type(gm).__name__}"
        )
    ggid = item.get("Gradient_Group_ID")
    if gm is False and ggid not in (None, ""):
        warnings.append(
            f"Item {i}: Gradient_Group_ID should be null when Gradient_Material is false"
        )

    _validate_composition(i, item.get("Composition_Info") or {}, errors)
    _validate_process(i, item.get("Process_Info") or {}, errors)
    _validate_microstructure(i, item.get("Microstructure_Info") or {}, errors, warnings)
    _validate_properties(i, item.get("Properties_Info") or [], errors, warnings)


def _validate_composition(i: int, ci: dict[str, Any], errors: list[str]) -> None:
    role = ci.get("Role")
    if role not in ("Target", "Reference"):
        errors.append(
            f"Item {i}: invalid Role '{role}' (must be 'Target' or 'Reference')"
        )

    for comp_key in ("Nominal_Composition", "Measured_Composition"):
        comp = ci.get(comp_key)
        if not isinstance(comp, dict):
            continue
        elems = comp.get("Elements_Normalized")
        if not elems:
            continue
        if not isinstance(elems, dict):
            errors.append(f"Item {i}: {comp_key}.Elements_Normalized must be dict or null")
            continue

        ct = comp.get("Composition_Type")
        if ct not in ("wt%", "at%"):
            errors.append(f"Item {i}: {comp_key} has invalid Composition_Type '{ct}'")

        # Per system prompt: when composition contains ranges/upper-limits (strings),
        # the sum check must be skipped — the Note field carries the explanation.
        if any(isinstance(v, str) for v in elems.values()):
            continue

        numeric_values = [v for v in elems.values() if isinstance(v, (int, float))]
        total = sum(numeric_values)
        if abs(total - 100) > 1:
            errors.append(
                f"Item {i}: {comp_key} sums to {total:.2f}% (must be 100 ± 1)"
            )
        other_val = elems.get("other")
        if isinstance(other_val, (int, float)) and other_val < 0:
            errors.append(
                f"Item {i}: {comp_key} 'other' is negative ({other_val}); must be omitted"
            )

    # Note field belongs at Composition_Info top level, not nested.
    for nested_key in ("Nominal_Composition", "Measured_Composition"):
        nested = ci.get(nested_key)
        if isinstance(nested, dict) and nested.get("Note") is not None:
            errors.append(
                f"Item {i}: Note field belongs at Composition_Info top level, "
                f"not inside {nested_key}"
            )


def _validate_process(i: int, pi: dict[str, Any], errors: list[str]) -> None:
    if not pi.get("Process_Category"):
        errors.append(f"Item {i}: Process_Info.Process_Category must be a non-empty string")
    pt = pi.get("Process_Text")
    if not isinstance(pt, dict):
        errors.append(f"Item {i}: Process_Text must be dict")
        return
    if not pt.get("original") and not pt.get("simplified"):
        errors.append(f"Item {i}: Process_Text has no original/simplified content")


def _validate_microstructure(
    i: int, mi: dict[str, Any], errors: list[str], warnings: list[str]
) -> None:
    aqf = mi.get("Advanced_Quantitative_Features")
    if aqf is not None and not isinstance(aqf, dict):
        errors.append(f"Item {i}: Advanced_Quantitative_Features must be dict")

    precipitates = mi.get("Precipitates") or []
    if not isinstance(precipitates, list):
        errors.append(f"Item {i}: Precipitates must be list")
    else:
        for idx, prec in enumerate(precipitates):
            if not isinstance(prec, dict):
                errors.append(f"Item {i}: Precipitates[{idx}] must be dict")
                continue
            if not prec.get("Phase_Type"):
                errors.append(
                    f"Item {i}: Precipitates[{idx}] missing 'Phase_Type' field"
                )
            vf = prec.get("Volume_Fraction_pct")
            if vf is None:
                continue
            if not isinstance(vf, (int, float)):
                errors.append(
                    f"Item {i}: Precipitates[{idx}].Volume_Fraction_pct must be "
                    f"number or null"
                )
            elif not (0 <= vf <= 100):
                errors.append(
                    f"Item {i}: Precipitates[{idx}].Volume_Fraction_pct={vf} "
                    f"out of [0,100]"
                )

    main_phase = mi.get("Main_Phase")
    if isinstance(main_phase, str) and main_phase.strip():
        token = _main_phase_violation(main_phase)
        if token:
            errors.append(
                f"Item {i}: Main_Phase '{main_phase}' looks like a secondary phase "
                f"('{token}'); use γ/FCC/BCC/austenite/... for the matrix and move "
                f"carbides/Laves into Precipitates[]"
            )

    rd = mi.get("Relative_Density_pct")
    if rd is None:
        return
    if not isinstance(rd, (int, float)):
        errors.append(f"Item {i}: Relative_Density_pct must be number or null")
        return
    if rd == 100.0:
        warnings.append(
            f"Item {i}: Relative_Density_pct=100% — verify this is explicitly "
            f"stated in the paper and not inferred"
        )
    elif not (0 < rd <= 100):
        errors.append(f"Item {i}: Relative_Density_pct={rd} out of (0,100]")


def _validate_properties(
    i: int, props: list[Any], errors: list[str], warnings: list[str]
) -> None:
    if not isinstance(props, list):
        errors.append(f"Item {i}: Properties_Info must be list")
        return

    # Track YS and UTS separately for tensile and compressive modes to avoid
    # cross-mode false positives when a paper reports both loading conditions.
    tensile_ys_mpa: float | None = None
    tensile_uts_mpa: float | None = None
    compressive_ys_mpa: float | None = None
    compressive_uts_mpa: float | None = None

    for j, p in enumerate(props):
        if not isinstance(p, dict):
            errors.append(f"Item {i}: Properties_Info[{j}] must be dict")
            continue

        pn = p.get("Property_Name") or ""
        if not pn:
            errors.append(f"Item {i}: Properties_Info[{j}] missing Property_Name")

        _check_test_temperature(i, p.get("Test_Temperature_K"), errors, warnings)

        val = p.get("Value_Numeric")
        unit = p.get("Unit")

        if unit == "%" and isinstance(val, (int, float)) and val > 200:
            errors.append(
                f"Item {i}: {pn}={val}% looks like MPa/GPa in a % field "
                f"(unit confusion)"
            )

        ds = p.get("Data_Source")
        if ds is not None and ds not in ("text", "image"):
            errors.append(
                f"Item {i}: Data_Source must be 'text' or 'image', got '{ds}'"
            )

        if "_compressive" in pn.lower() and "_Compressive" not in pn:
            errors.append(
                f"Item {i}: Property_Name '{pn}' has wrong casing; "
                f"use exact '_Compressive' suffix"
            )

        if pn.startswith("Elongation") and isinstance(val, (int, float)):
            if val < 0 or val > 100:
                errors.append(f"Item {i}: {pn}={val}% out of [0,100]")

        # Collect YS/UTS per loading mode for physical-constraint cross-check.
        if isinstance(val, (int, float)) and unit in ("MPa", "GPa"):
            value_mpa = val * (1000.0 if unit == "GPa" else 1.0)
            if pn == "Yield_Strength":
                tensile_ys_mpa = value_mpa
            elif pn == "Ultimate_Tensile_Strength":
                tensile_uts_mpa = value_mpa
            elif pn == "Yield_Strength_Compressive":
                compressive_ys_mpa = value_mpa
            elif pn == "Ultimate_Compressive_Strength":
                compressive_uts_mpa = value_mpa

    # YS ≤ UTS check within each loading mode independently.
    for mode, ys, uts in (
        ("tensile", tensile_ys_mpa, tensile_uts_mpa),
        ("compressive", compressive_ys_mpa, compressive_uts_mpa),
    ):
        if ys is not None and uts is not None and ys > uts * 1.01:
            warnings.append(
                f"Item {i}: {mode} Yield_Strength ({ys:.0f} MPa) exceeds "
                f"Ultimate_Strength ({uts:.0f} MPa); verify units and assignment"
            )


def _check_test_temperature(
    i: int, tt: Any, errors: list[str], warnings: list[str]
) -> None:
    """Flag suspected °C values masquerading as K, while allowing cryogenic tests."""
    if tt is None:
        return
    if not isinstance(tt, (int, float)):
        errors.append(f"Item {i}: Test_Temperature_K must be number or null")
        return
    if 15 <= tt <= 45:
        warnings.append(
            f"Item {i}: Test_Temperature_K={tt} looks like °C "
            f"(room temperature in K = 298.15)"
        )
    elif tt < 4:
        warnings.append(
            f"Item {i}: Test_Temperature_K={tt} is below liquid-helium range; verify"
        )


def _load(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save_json(data: dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _save_issue_log(path: str, errors: list[str], warnings: list[str]) -> None:
    lines = [
        "# Validation Issues",
        "",
        f"- errors: {len(errors)}",
        f"- warnings: {len(warnings)}",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.extend(f"- {e}" for e in errors)
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        lines.extend(f"- {w}" for w in warnings)
        lines.append("")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Validate extraction JSON against schema."
    )
    parser.add_argument("input", help="input extraction JSON path")
    parser.add_argument(
        "output", nargs="?", help="output validated JSON path (default: overwrite input)"
    )
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as errors"
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        data = _load(args.input)
    except (OSError, json.JSONDecodeError) as e:
        logger.error("failed to load %s: %s", args.input, e)
        return 2

    errors, warnings = validate(data)

    for w in warnings:
        logger.warning(w)
    for e in errors:
        logger.error(e)

    # Always write output so review/revise steps can still run on the data.
    output_path = args.output or args.input
    try:
        _save_json(data, output_path)
    except OSError as e:
        logger.error("failed to write %s: %s", output_path, e)
        return 2

    if output_path != args.input and (errors or warnings):
        log_path = output_path.replace(".json", "_issues.md")
        _save_issue_log(log_path, errors, warnings)

    if errors or (args.strict and warnings):
        logger.error(
            "validation failed: %d errors, %d warnings", len(errors), len(warnings)
        )
        return 1

    logger.info(
        "validation passed: %d warnings -> %s", len(warnings), output_path
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
