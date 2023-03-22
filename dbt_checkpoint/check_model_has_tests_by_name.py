import argparse
import os
import time
from itertools import groupby
from typing import Any, Dict, Optional, Sequence

from dbt_checkpoint.tracking import dbtCheckpointTracking
from dbt_checkpoint.utils import (
    JsonOpenError,
    ParseDict,
    Test,
    add_default_args,
    get_json,
    get_missing_file_paths,
    get_model_sqls,
    get_models,
    get_parent_childs,
)


def check_test_cnt(
    paths: Sequence[str], manifest: Dict[str, Any], required_tests: Dict[str, int], discover_files: bool
) -> int:
    if discover_files:
        paths = get_missing_file_paths(paths, manifest)
    status_code = 0
    sqls = get_model_sqls(paths, manifest)
    filenames = set(sqls.keys())

    # get manifest nodes that pre-commit found as changed
    models = get_models(manifest, filenames)

    for model in models:
        childs = list(
            get_parent_childs(
                manifest=manifest,
                obj=model,
                manifest_node="child_map",
                node_types=["test"],
            )
        )
        tests = [test for test in childs if isinstance(test, Test)]
        grouped = groupby(
            sorted(tests, key=lambda x: x.test_name), lambda x: x.test_name
        )
        test_dict = {key: list(value) for key, value in grouped}
        for required_test, required_cnt in required_tests.items():
            test = test_dict.get(required_test, [])
            test_cnt = len(test)
            if not test or required_cnt > test_cnt:
                status_code = 1
                print(
                    f"{model.model_name}: "
                    f"has only {test_cnt} {required_test} tests, but "
                    f"{required_cnt} are required.",
                )
    return status_code


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    add_default_args(parser)

    parser.add_argument(
        "--tests",
        metavar="KEY=VALUE",
        nargs="+",
        required=True,
        help="Set a number of key-value pairs."
        " Key is name of test and value is required "
        "minimal number of tests eg. --test unique=1 not_null=2"
        "(do not put spaces before or after the = sign)."
        "",
        action=ParseDict,
    )

    args = parser.parse_args(argv)

    try:
        manifest = get_json(args.manifest)
    except JsonOpenError as e:
        print(f"Unable to load manifest file ({e})")
        return 1

    start_time = time.time()
    required_tests = {}
    for test_type, cnt in args.tests.items():
        try:
            test_cnt = int(cnt)
        except ValueError:
            parser.error(f"Unable to cast {cnt} to int.")
        required_tests[test_type] = test_cnt

    end_time = time.time()

    status_code = check_test_cnt(
        paths=args.filenames, manifest=manifest, required_tests=required_tests, discover_files=args.discover_files
    )
    script_args = vars(args)

    tracker = dbtCheckpointTracking(script_args=script_args)
    tracker.track_hook_event(
        event_name="Hook Executed",
        manifest=manifest,
        event_properties={
            "hook_name": os.path.basename(__file__),
            "description": "Check model has tests by name",
            "status": status_code,
            "execution_time": end_time - start_time,
            "is_pytest": script_args.get("is_test"),
        },
    )

    return status_code


if __name__ == "__main__":
    exit(main())
