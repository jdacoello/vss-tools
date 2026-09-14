# Copyright (c) 2023 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_UNITS = HERE / ".." / "test_units.yaml"
TEST_QUANT = HERE / ".." / "test_quantities.yaml"


def test_skeleton_free_overlay_merges_attributes_and_adds_nodes(tmp_path):
    """
    A subsequent --types file with no root-level declaration at all should
    be treated as an overlay: it may add new attributes to already-defined
    struct fields, and attach brand new nodes, without redeclaring the root
    branch or any part of the existing skeleton.
    """
    output = tmp_path / "out.json"
    base = HERE / "base.vspec"
    overlay = HERE / "overlay_no_root.vspec"
    spec = HERE / "test.vspec"
    cmd = f"vspec export json --pretty --types {base} --types {overlay}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output} -e binding"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr

    data = json.loads(output.read_text())
    types = data["ComplexDataTypes"]["Types"]["children"]
    assert types["Struct1"]["children"]["x"]["binding"] == "2nl"
    assert "NewBranch" in types
    assert types["NewBranch"]["children"]["NewStruct"]["children"]["value"]["datatype"] == "string"


def test_matching_root_overlay_merges_attributes(tmp_path):
    """
    A subsequent --types file that redeclares the same root as an already
    established types tree should also merge attributes into already-defined
    nodes instead of being silently discarded.
    """
    output = tmp_path / "out.json"
    base = HERE / "base.vspec"
    overlay = HERE / "overlay_with_root.vspec"
    spec = HERE / "test.vspec"
    cmd = f"vspec export json --pretty --types {base} --types {overlay}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output} -e binding"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode == 0, process.stderr

    data = json.loads(output.read_text())
    types = data["ComplexDataTypes"]["Types"]["children"]
    assert types["Struct1"]["children"]["y"]["binding"] == "2nm"


def test_mismatched_root_still_raises_multiple_type_trees_exception(tmp_path):
    """
    A subsequent --types file declaring a genuinely different root must
    still be rejected, with an insightful message naming both roots.
    """
    output = tmp_path / "out.json"
    base = HERE / "base.vspec"
    overlay = HERE / "overlay_mismatched_root.vspec"
    spec = HERE / "test.vspec"
    cmd = f"vspec export json --pretty --types {base} --types {overlay}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output}"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "MultipleTypeTreesException" in process.stderr
    assert "Types" in process.stderr
    assert "OtherTypes" in process.stderr


def test_overlay_without_prior_root_raises_dedicated_exception(tmp_path):
    """
    An overlay-only --types file (no root declaration) passed without any
    prior --types file establishing a types tree must raise a dedicated,
    insightful exception rather than a generic 'no roots' error.
    """
    output = tmp_path / "out.json"
    overlay = HERE / "overlay_no_root.vspec"
    spec = HERE / "test.vspec"
    cmd = f"vspec export json --pretty --types {overlay}"
    cmd += f" -u {TEST_UNITS} -q {TEST_QUANT} --vspec {spec} --output {output} -e binding"
    process = subprocess.run(cmd.split(), capture_output=True, text=True)
    assert process.returncode != 0
    assert "TypesOverlayWithoutRootException" in process.stderr
