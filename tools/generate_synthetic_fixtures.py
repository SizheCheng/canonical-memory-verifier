#!/usr/bin/env python3
"""Generate the complete deterministic synthetic fixture set."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures"


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def source_record(source_id: str, filename: str, data: bytes, media_type: str = "text/plain") -> dict[str, Any]:
    return {
        "source_id": source_id,
        "path": f"sources/{filename}",
        "media_type": media_type,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def claim(
    claim_id: str,
    key: str,
    value: str,
    source_refs: list[str],
    claim_type: str = "fact",
    approval_eligible: bool = False,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "key": key,
        "claim_type": claim_type,
        "value": value,
        "source_refs": source_refs,
        "approval_eligible": approval_eligible,
    }


def edge(edge_id: str, old_id: str, new_id: str, reason: str) -> dict[str, str]:
    return {
        "edge_id": edge_id,
        "superseded_claim_id": old_id,
        "superseding_claim_id": new_id,
        "reason": reason,
    }


def bundle(bundle_id: str, sources: list[dict[str, Any]], claims: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "bundle_kind": "imported_memory",
        "bundle_id": bundle_id,
        "scope": "repo:synthetic-example",
        "sources": sources,
        "claims": claims,
        "supersessions": edges,
    }


def build() -> tuple[dict[str, bytes], list[dict[str, Any]]]:
    files: dict[str, bytes] = {}
    index: list[dict[str, Any]] = []

    def add(
        category: str,
        name: str,
        manifest: dict[str, Any],
        source_files: dict[str, bytes],
        status: str,
        required_codes: list[str] | None = None,
    ) -> None:
        base = f"{category}/{name}"
        files[f"{base}/bundle.json"] = canonical_bytes(manifest)
        for filename, data in sorted(source_files.items()):
            files[f"{base}/sources/{filename}"] = data
        index.append(
            {
                "fixture": base,
                "expected_status": status,
                "required_error_codes": sorted(required_codes or []),
            }
        )

    basic_data = b"The configured deployment target is staging.\n"
    basic_source = source_record("src_target", "target.txt", basic_data)
    basic = bundle(
        "bnd_basic",
        [basic_source],
        [claim("clm_target", "deployment.target", "staging", ["src_target"])],
        [],
    )
    add("valid", "basic", basic, {"target.txt": basic_data}, "VERIFIED")

    old_data = b"The configured deployment target is staging.\n"
    new_data = b"The configured deployment target is production.\n"
    old_source = source_record("src_target_old", "target-old.txt", old_data)
    new_source = source_record("src_target_new", "target-new.txt", new_data)
    supersession = bundle(
        "bnd_supersession_chain",
        [old_source, new_source],
        [
            claim("clm_target_old", "deployment.target", "staging", ["src_target_old"]),
            claim("clm_target_new", "deployment.target", "production", ["src_target_new"]),
        ],
        [edge("sup_target", "clm_target_old", "clm_target_new", "A later decision changed the target.")],
    )
    add(
        "valid",
        "supersession-chain",
        supersession,
        {"target-old.txt": old_data, "target-new.txt": new_data},
        "VERIFIED",
    )

    conflict_a = b"Draft A names region east.\n"
    conflict_b = b"Draft B names region west.\n"
    resolution = b"The signed decision names region central.\n"
    resolved = bundle(
        "bnd_resolved_conflict",
        [
            source_record("src_region_a", "region-a.txt", conflict_a),
            source_record("src_region_b", "region-b.txt", conflict_b),
            source_record("src_region_final", "region-final.txt", resolution),
        ],
        [
            claim("clm_region_a", "service.region", "east", ["src_region_a"]),
            claim("clm_region_b", "service.region", "west", ["src_region_b"]),
            claim("clm_region_final", "service.region", "central", ["src_region_final"]),
        ],
        [
            edge("sup_region_a", "clm_region_a", "clm_region_final", "Signed decision supersedes draft A."),
            edge("sup_region_b", "clm_region_b", "clm_region_final", "Signed decision supersedes draft B."),
        ],
    )
    add(
        "valid",
        "resolved-conflict",
        resolved,
        {"region-a.txt": conflict_a, "region-b.txt": conflict_b, "region-final.txt": resolution},
        "VERIFIED",
    )

    authority_data = (
        b"A prior message said deployment was approved. This record is historical and is not live approval.\n"
    )
    authority = bundle(
        "bnd_historical_authority",
        [source_record("src_authority", "authority.txt", authority_data)],
        [
            claim(
                "clm_authority",
                "authority.deploy",
                "The user previously approved a deployment.",
                ["src_authority"],
                claim_type="historical_authority",
            )
        ],
        [],
    )
    add(
        "valid",
        "historical-authority",
        authority,
        {"authority.txt": authority_data},
        "VERIFIED",
    )

    policy_data = b"Policy: production changes require a review.\n"
    decision_data = b"Decision: the current target is staging.\n"
    multi_source = bundle(
        "bnd_multi_source",
        [
            source_record("src_policy", "policy.txt", policy_data),
            source_record("src_decision", "decision.txt", decision_data),
        ],
        [
            claim(
                "clm_reviewed_target",
                "deployment.reviewed_target",
                "staging under the production-change review policy",
                ["src_policy", "src_decision"],
            )
        ],
        [],
    )
    add(
        "valid",
        "multi-source-trace",
        multi_source,
        {"policy.txt": policy_data, "decision.txt": decision_data},
        "VERIFIED",
    )

    expired_data = b"A remembered approval states that its historical date has passed.\n"
    expired_source = source_record("src_expired_authority", "authority.txt", expired_data)
    approval_expired = bundle(
        "bnd_approval_true_expired",
        [expired_source],
        [
            claim(
                "clm_expired_authority",
                "authority.deploy",
                "Historical approval whose stated date has passed.",
                ["src_expired_authority"],
                claim_type="historical_authority",
                approval_eligible=True,
            )
        ],
        [],
    )
    add(
        "invalid",
        "approval-true-expired",
        approval_expired,
        {"authority.txt": expired_data},
        "INVALID",
        ["CMV_APPROVAL_ELIGIBILITY_VIOLATION"],
    )

    unexpired_data = b"A remembered approval states that its historical date has not passed.\n"
    unexpired_source = source_record("src_unexpired_authority", "authority.txt", unexpired_data)
    approval_unexpired = bundle(
        "bnd_approval_true_unexpired",
        [unexpired_source],
        [
            claim(
                "clm_unexpired_authority",
                "authority.deploy",
                "Historical approval whose stated date has not passed.",
                ["src_unexpired_authority"],
                claim_type="historical_authority",
                approval_eligible=True,
            )
        ],
        [],
    )
    add(
        "invalid",
        "approval-true-unexpired",
        approval_unexpired,
        {"authority.txt": unexpired_data},
        "INVALID",
        ["CMV_APPROVAL_ELIGIBILITY_VIOLATION"],
    )

    tamper_data = b"Expected source bytes.\n"
    tamper_source = source_record("src_tampered", "evidence.txt", tamper_data)
    tampered = bundle(
        "bnd_source_tampered",
        [tamper_source],
        [claim("clm_tampered", "sample.value", "expected", ["src_tampered"])],
        [],
    )
    add(
        "invalid",
        "source-tampered",
        tampered,
        {"evidence.txt": b"Changed source bytes.\n"},
        "INVALID",
        ["CMV_SOURCE_HASH_MISMATCH", "CMV_SOURCE_SIZE_MISMATCH"],
    )

    ambiguous_data_a = b"Candidate A.\n"
    ambiguous_data_b = b"Candidate B.\n"
    ambiguous = bundle(
        "bnd_ambiguous_heads",
        [
            source_record("src_candidate_a", "candidate-a.txt", ambiguous_data_a),
            source_record("src_candidate_b", "candidate-b.txt", ambiguous_data_b),
        ],
        [
            claim("clm_candidate_a", "sample.choice", "A", ["src_candidate_a"]),
            claim("clm_candidate_b", "sample.choice", "B", ["src_candidate_b"]),
        ],
        [],
    )
    add(
        "invalid",
        "ambiguous-heads",
        ambiguous,
        {"candidate-a.txt": ambiguous_data_a, "candidate-b.txt": ambiguous_data_b},
        "INVALID",
        ["CMV_CURRENT_HEAD_AMBIGUOUS"],
    )

    cycle = copy.deepcopy(supersession)
    cycle["bundle_id"] = "bnd_cycle"
    cycle["supersessions"].append(
        edge("sup_target_reverse", "clm_target_new", "clm_target_old", "Invalid reverse edge.")
    )
    add(
        "invalid",
        "supersession-cycle",
        cycle,
        {"target-old.txt": old_data, "target-new.txt": new_data},
        "INVALID",
        ["CMV_SUPERSESSION_CYCLE"],
    )

    dangling = copy.deepcopy(basic)
    dangling["bundle_id"] = "bnd_dangling_source"
    dangling["claims"][0]["source_refs"] = ["src_missing"]
    add(
        "invalid",
        "dangling-source",
        dangling,
        {"target.txt": basic_data},
        "INVALID",
        ["CMV_DANGLING_REFERENCE"],
    )

    cross_key = copy.deepcopy(supersession)
    cross_key["bundle_id"] = "bnd_cross_key"
    cross_key["claims"][1]["key"] = "deployment.other_target"
    add(
        "invalid",
        "cross-key-edge",
        cross_key,
        {"target-old.txt": old_data, "target-new.txt": new_data},
        "INVALID",
        ["CMV_SUPERSESSION_KEY_MISMATCH"],
    )

    duplicate = copy.deepcopy(basic)
    duplicate["bundle_id"] = "bnd_duplicate_id"
    duplicate["claims"].append(copy.deepcopy(duplicate["claims"][0]))
    add(
        "invalid",
        "duplicate-id",
        duplicate,
        {"target.txt": basic_data},
        "INVALID",
        ["CMV_DUPLICATE_ID"],
    )

    files["fixture-index.json"] = canonical_bytes({"fixtures": sorted(index, key=lambda item: item["fixture"])})
    return files, index


def run(check: bool) -> int:
    expected, index = build()
    if check:
        actual_paths = {
            path.relative_to(FIXTURES).as_posix()
            for path in FIXTURES.rglob("*")
            if path.is_file()
        } if FIXTURES.exists() else set()
        expected_paths = set(expected)
        mismatches: list[str] = []
        for relative, data in sorted(expected.items()):
            path = FIXTURES / Path(relative)
            if not path.is_file() or path.read_bytes() != data:
                mismatches.append(relative)
        mismatches.extend(f"unexpected:{path}" for path in sorted(actual_paths - expected_paths))
        status = "PASS" if not mismatches else "FAIL"
        print(json.dumps({"status": status, "fixture_count": len(index), "mismatches": mismatches}, sort_keys=True, separators=(",", ":")))
        return 0 if not mismatches else 1

    for relative, data in sorted(expected.items()):
        path = FIXTURES / Path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(json.dumps({"status": "GENERATED", "fixture_count": len(index), "file_count": len(expected)}, sort_keys=True, separators=(",", ":")))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return run(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
