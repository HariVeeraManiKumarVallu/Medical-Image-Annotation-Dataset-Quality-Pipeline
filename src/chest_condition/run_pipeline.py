from __future__ import annotations

import argparse

from src.nih_sample.run_pipeline import run as _run


def run(config_path: str = "configs/chest_condition.yaml") -> None:
    _run(config_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/chest_condition.yaml")
    run(parser.parse_args().config)