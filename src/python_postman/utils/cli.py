import argparse


class Cli:
    def __init__(self) -> None:
        pass

    @property
    def envs(self):
        envs: list = ["temp", "dev", "prod", "qa"]
        return envs

    def parse_arguments(self):
        # setup parser
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-e",
            "--environment",
            type=str,
            required=True,
            help="target environment",
            choices=self.envs,
        )
        parser.add_argument(
            "-t",
            "--tag",
            type=str,
            required=False,
            help="Tag that determines which tagged flow runs, select from the flows corresponding model flow.",
        )

        parser.add_argument(
            "--select",
            metavar="SELECT",
            type=str,
            nargs="*",
            required=False,
            help="Select allows you to select multiple tags, ex: --select tag:tag1 tag:tag2 tag:tag3",
            default=[],
        )

        parser.add_argument(
            "--args",
            metavar="ARGS",
            type=str,
            nargs="*",
            required=False,
            help="Additional arguments to pass to the flow, ex: --args arg1 arg2 arg3",
            default=[],
        )

        parser.add_argument(
            "-r",
            "--refresh",
            type=str,
            required=False,
            help="Add a date to refresh the data.",
        )
        # get args
        args = parser.parse_args()

        return args
