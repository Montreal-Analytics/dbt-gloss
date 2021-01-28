import argparse
from typing import List
from typing import Optional
from typing import Sequence

from pre_commit_dbt.utils import add_dbt_cmd_args
from pre_commit_dbt.utils import add_dbt_cmd_model_args
from pre_commit_dbt.utils import add_filenames_args
from pre_commit_dbt.utils import paths_to_dbt_models
from pre_commit_dbt.utils import run_dbt_cmd


def prepare_cmd(
    paths: Sequence[str],
    global_flags: Optional[Sequence[str]] = None,
    cmd_flags: Optional[Sequence[str]] = None,
    prefix: str = "",
    postfix: str = "",
) -> List[str]:
    global_flags = global_flags or []
    cmd_flags = cmd_flags or []
    dbt_models = paths_to_dbt_models(paths, prefix, postfix)
    cmd = ["dbt", *global_flags, "test", "-m", *dbt_models, *cmd_flags]
    return cmd


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    add_filenames_args(parser)
    add_dbt_cmd_args(parser)
    add_dbt_cmd_model_args(parser)

    args = parser.parse_args(argv)

    cmd = prepare_cmd(
        args.filenames,
        args.global_flags,
        args.cmd_flags,
        args.model_prefix,
        args.model_postfix,
    )
    return run_dbt_cmd(cmd)


if __name__ == "__main__":
    exit(main())
