import argparse


class Cli:
    def __init__(self) -> None:
        pass

    @property
    def envs(self):
        envs: list = ["temp", "dev", "prod"]
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
            "-r",
            "--refresh",
            type=str,
            required=False,
            help="",
            choices=["full"],
        )
        # get args
        args = parser.parse_args()

        return args
