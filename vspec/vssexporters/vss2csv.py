#!/usr/bin/env python3

# Copyright (c) 2021 Contributors to COVESA
#
# This program and the accompanying materials are made available under the
# terms of the Mozilla Public License 2.0 which is available at
# https://www.mozilla.org/en-US/MPL/2.0/
#
# SPDX-License-Identifier: MPL-2.0

# Convert vspec tree to CSV


import argparse
import logging
from vspec.model.vsstree import VSSNode
from anytree import PreOrderIter  # type: ignore[import]
from typing import AnyStr
from typing import Optional
from vspec.vss2x import Vss2X
from vspec.vspec2vss_config import Vspec2VssConfig


# Write the header line


def print_csv_header(file, uuid: bool, entry_type: AnyStr, include_instance_column: bool, extended_attributes: set):
    arg_list = [entry_type, "Type", "DataType", "Deprecated", "Unit",
                "Min", "Max", "Desc", "Comment", "Allowed", "Default"]
    if uuid:
        arg_list.append("Id")
    if include_instance_column:
        arg_list.append("Instances")

    if extended_attributes:
        arg_list.extend(extended_attributes)
    file.write(format_csv_line(arg_list))

# Format a data or header line according to the CSV standard (IETF RFC 4180)


def format_csv_line(csv_fields):
    formatted_csv_line = ""
    for csv_field in csv_fields:
        formatted_csv_line = formatted_csv_line + '"' + str(csv_field).replace('"', '""') + '",'
    return formatted_csv_line[:-1] + '\n'

# Write the data lines


def print_csv_content(file, config, tree: VSSNode, uuid, include_instance_column: bool, extended_attributes: set):
    tree_node: VSSNode
    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.get_datatype()
        unit_str = tree_node.get_unit()
        arg_list = [tree_node.qualified_name('.'), tree_node.type.value, data_type_str, tree_node.deprecation,
                    unit_str, tree_node.min, tree_node.max, tree_node.description, tree_node.comment,
                    tree_node.allowed, tree_node.default]
        if uuid:
            arg_list.append(tree_node.uuid)
        if include_instance_column and tree_node.instances is not None:
            arg_list.append(tree_node.instances)

        ext_attr_dict = {}
        for k, v in tree_node.extended_attributes.items():
            if not config.csv_all_extended_attributes and k not in VSSNode.whitelisted_extended_attributes:
                continue
            ext_attr_dict[k] = v

        for attr in extended_attributes:
            arg_list.append(ext_attr_dict.get(attr, ""))

        file.write(format_csv_line(arg_list))


class Vss2Csv(Vss2X):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('--csv-all-extended-attributes', action='store_true',
                            help=("Generate all extended attributes found in the model "
                                  "(default is generating only those given by the "
                                  "-e/--extended-attributes parameter)."))

    def generate(self, config: argparse.Namespace, signal_root: VSSNode, vspec2vss_config: Vspec2VssConfig,
                 data_type_root: Optional[VSSNode] = None) -> None:
        logging.info("Generating CSV output...")

        # generic entry should be written when both data types and signals are being written to the same file
        generic_entry = data_type_root is not None and config.types_output_file is None
        include_instance_column = not vspec2vss_config.expand_model
        extended_attributes = get_extended_attributes(signal_root, config)
        with open(config.output_file, 'w') as f:
            signal_entry_type = "Node" if generic_entry else "Signal"
            print_csv_header(f, vspec2vss_config.generate_uuid, signal_entry_type, include_instance_column, extended_attributes)
            print_csv_content(f, config, signal_root, vspec2vss_config.generate_uuid, include_instance_column, extended_attributes)
            if data_type_root is not None and generic_entry is True:
                print_csv_content(f, config, data_type_root, vspec2vss_config.generate_uuid, include_instance_column, extended_attributes)

        if data_type_root is not None and generic_entry is False:
            with open(config.types_output_file, 'w') as f:
                print_csv_header(f, vspec2vss_config.generate_uuid, "Node", include_instance_column, extended_attributes)
                print_csv_content(f, config, data_type_root, vspec2vss_config.generate_uuid, include_instance_column, extended_attributes)

def get_extended_attributes(tree: VSSNode, config: argparse.Namespace):
    extended_attributes = set()
    for tree_node in PreOrderIter(tree):
        for k, v in tree_node.extended_attributes.items():
            if not config.csv_all_extended_attributes and k not in VSSNode.whitelisted_extended_attributes:
                continue
            extended_attributes.add(k)

    return sorted(extended_attributes)
