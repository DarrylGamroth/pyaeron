#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HEADER = ROOT.parent / "aeron" / "aeron-client" / "src" / "main" / "c" / "aeronc.h"
DEFAULT_OUTPUT = ROOT / "pyaeron" / "_generated_cdef.py"

PRIMITIVES = """typedef _Bool bool;
typedef long int ssize_t;
typedef unsigned char uint8_t;
typedef signed char int8_t;
typedef signed short int16_t;
typedef unsigned short uint16_t;
typedef signed int int32_t;
typedef unsigned int uint32_t;
typedef signed long int int64_t;
typedef unsigned long int uint64_t;
typedef unsigned long size_t;
"""

REQUIRED_DECLARATIONS = {
    # Types
    "aeron_context_t",
    "aeron_t",
    "aeron_publication_t",
    "aeron_exclusive_publication_t",
    "aeron_subscription_t",
    "aeron_image_t",
    "aeron_counter_t",
    "aeron_counters_reader_t",
    "aeron_cnc_t",
    "aeron_header_t",
    "aeron_header_values_frame_stct",
    "aeron_header_values_frame_t",
    "aeron_async_add_publication_t",
    "aeron_async_add_exclusive_publication_t",
    "aeron_async_add_subscription_t",
    "aeron_async_add_counter_t",
    "aeron_async_destination_t",
    "aeron_header_values_t",
    "aeron_buffer_claim_t",
    "aeron_counter_constants_t",
    "aeron_image_constants_t",
    "aeron_cnc_constants_t",
    # Callback typedefs
    "aeron_reserved_value_supplier_t",
    "aeron_fragment_handler_t",
    "aeron_error_log_reader_func_t",
    "aeron_on_available_image_t",
    "aeron_on_unavailable_image_t",
    "aeron_notification_t",
    # Functions
    "aeron_context_init",
    "aeron_context_close",
    "aeron_context_set_dir",
    "aeron_context_get_dir",
    "aeron_context_set_driver_timeout_ms",
    "aeron_context_get_driver_timeout_ms",
    "aeron_context_set_keepalive_interval_ns",
    "aeron_context_get_keepalive_interval_ns",
    "aeron_context_set_resource_linger_duration_ns",
    "aeron_context_get_resource_linger_duration_ns",
    "aeron_context_set_idle_sleep_duration_ns",
    "aeron_context_get_idle_sleep_duration_ns",
    "aeron_context_set_pre_touch_mapped_memory",
    "aeron_context_get_pre_touch_mapped_memory",
    "aeron_context_set_client_name",
    "aeron_context_get_client_name",
    "aeron_context_set_use_conductor_agent_invoker",
    "aeron_context_get_use_conductor_agent_invoker",
    "aeron_init",
    "aeron_start",
    "aeron_main_do_work",
    "aeron_main_idle_strategy",
    "aeron_close",
    "aeron_is_closed",
    "aeron_client_id",
    "aeron_next_correlation_id",
    "aeron_async_add_publication",
    "aeron_async_add_publication_poll",
    "aeron_async_add_exclusive_publication",
    "aeron_async_add_exclusive_publication_poll",
    "aeron_async_add_subscription",
    "aeron_async_add_subscription_poll",
    "aeron_async_add_counter",
    "aeron_async_add_counter_poll",
    "aeron_publication_offer",
    "aeron_publication_is_closed",
    "aeron_publication_is_connected",
    "aeron_publication_close",
    "aeron_publication_try_claim",
    "aeron_publication_async_add_destination",
    "aeron_publication_async_remove_destination",
    "aeron_publication_async_destination_poll",
    "aeron_exclusive_publication_offer",
    "aeron_exclusive_publication_try_claim",
    "aeron_exclusive_publication_is_closed",
    "aeron_exclusive_publication_is_connected",
    "aeron_exclusive_publication_close",
    "aeron_exclusive_publication_async_add_destination",
    "aeron_exclusive_publication_async_remove_destination",
    "aeron_exclusive_publication_async_destination_poll",
    "aeron_buffer_claim_commit",
    "aeron_buffer_claim_abort",
    "aeron_subscription_poll",
    "aeron_subscription_is_closed",
    "aeron_subscription_is_connected",
    "aeron_subscription_close",
    "aeron_subscription_async_add_destination",
    "aeron_subscription_async_remove_destination",
    "aeron_subscription_async_destination_poll",
    "aeron_subscription_image_count",
    "aeron_subscription_image_by_session_id",
    "aeron_subscription_image_release",
    "aeron_header_values",
    "aeron_header_position",
    "aeron_image_constants",
    "aeron_image_position",
    "aeron_image_is_closed",
    "aeron_counters_reader",
    "aeron_counters_reader_max_counter_id",
    "aeron_counters_reader_addr",
    "aeron_counter_constants",
    "aeron_counter_addr",
    "aeron_counter_close",
    "aeron_counter_is_closed",
    "aeron_cnc_init",
    "aeron_cnc_constants",
    "aeron_cnc_filename",
    "aeron_cnc_to_driver_heartbeat",
    "aeron_cnc_error_log_read",
    "aeron_cnc_counters_reader",
    "aeron_cnc_close",
    "aeron_errcode",
    "aeron_errmsg",
}


def _strip_comments_and_directives(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    lines = []
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        if 'extern "C"' in stripped:
            continue
        lines.append(line)
    return "\n".join(lines)


def _split_top_level_statements(text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    brace_depth = 0

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # Ignore unmatched braces from removed preprocessor blocks (e.g. extern "C").
        if stripped == "{" and brace_depth == 0 and not current:
            continue
        if stripped == "}" and brace_depth == 0:
            continue

        current.append(line)
        brace_depth += line.count("{")
        brace_depth -= line.count("}")
        if brace_depth < 0:
            brace_depth = 0

        if brace_depth == 0 and ";" in line:
            statement = "\n".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

    return statements


def _declaration_name(statement: str) -> str | None:
    statement = statement.strip()
    struct_match = re.match(r"struct\s+([A-Za-z_]\w*)\s*\{", statement)
    if struct_match:
        return struct_match.group(1)

    if statement.startswith("typedef"):
        fp_match = re.search(r"\(\s*\*\s*([A-Za-z_]\w*)\s*\)", statement)
        if fp_match:
            return fp_match.group(1)

        alias_match = re.search(r"([A-Za-z_]\w*)\s*;\s*$", statement)
        if alias_match:
            return alias_match.group(1)
        return None

    fn_match = re.search(r"([A-Za-z_]\w*)\s*\([^;]*\)\s*;\s*$", statement, flags=re.S)
    if fn_match:
        return fn_match.group(1)
    return None


def _extract_required_declarations(header_path: Path) -> list[str]:
    raw = header_path.read_text(encoding="utf-8")
    clean = _strip_comments_and_directives(raw)
    statements = _split_top_level_statements(clean)
    selected_by_name: dict[str, str] = {}
    order: list[str] = []
    for statement in statements:
        name = _declaration_name(statement)
        if name is None:
            continue
        if name not in REQUIRED_DECLARATIONS:
            continue

        existing = selected_by_name.get(name)
        if existing is None:
            selected_by_name[name] = statement
            order.append(name)
            continue

        # Prefer concrete struct definitions over forward typedef declarations.
        is_existing_forward = existing.startswith("typedef struct") and "{" not in existing
        is_new_definition = statement.startswith("typedef struct") and "{" in statement
        if is_existing_forward and is_new_definition:
            selected_by_name[name] = statement

    missing = sorted(REQUIRED_DECLARATIONS - set(selected_by_name))
    if missing:
        raise RuntimeError("Missing declarations in header extraction: " + ", ".join(missing))

    return [selected_by_name[name] for name in order]


def _render_output(header_path: Path, declarations: list[str]) -> str:
    cdef_body = PRIMITIVES + "\n\n" + "\n\n".join(declarations) + "\n"
    return (
        '"""Generated cffi cdef declarations.\n\n'
        f"Source: {header_path}\n"
        'Do not edit manually; run `scripts/generate_cdef.py`.\n"""\n\n'
        "CDEF = r'''\n"
        f"{cdef_body}"
        "'''\n"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pyaeron cffi cdef declarations from aeronc.h"
    )
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    declarations = _extract_required_declarations(args.header)
    output = _render_output(args.header, declarations)
    args.output.write_text(output, encoding="utf-8")
    print(f"Wrote {args.output} from {args.header}")


if __name__ == "__main__":
    main()
