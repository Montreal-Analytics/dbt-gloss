import argparse
import os
import time
from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import Sequence

from pre_commit_dbt.tracking import dbtCheckpointTracking
from pre_commit_dbt.utils import add_filenames_args
from pre_commit_dbt.utils import get_source_schemas
from pre_commit_dbt.utils import red


def has_loader(paths: Sequence[str]) -> int:
    status_code = 0
    ymls = [Path(path) for path in paths]

    # if user added schema but did not rerun
    schemas = get_source_schemas(ymls)

    for schema in schemas:
        if not schema.source_schema.get("loader"):
            status_code = 1
            print(
                f"{red(f'{schema.source_name}.{schema.table_name}')}: "
                f"does not have defined loader.",
            )
    return status_code


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    add_filenames_args(parser)

    args = parser.parse_args(argv)

    return has_loader(paths=args.filenames)


if __name__ == "__main__":
    exit(main())
