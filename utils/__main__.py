"""Command-line execution of the utils package."""

from collections.abc import Sequence

__all__: Sequence[str] = ()

from utils import InviteURLGenerator, main

if __name__ == "__main__":
    raise SystemExit(main(utility_functions={InviteURLGenerator}))
