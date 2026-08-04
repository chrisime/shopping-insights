#!/usr/bin/env python3
"""The acceptance suite entry point for the Python stack.

This is the peer of the JS stack's cucumber.cjs. cucumber-js loads its config
as executable JavaScript, so it can extract the Gherkin at config-load time and
`npm test` stays a plain `cucumber-js` call. behave has no such hook --
behave.ini is INI, not code -- and, crucially, behave collects and parses the
feature files BEFORE environment.py's before_all fires. Extracting from
before_all would therefore have behave parse a stale (or absent) .extracted/
tree and only then rebuild it: exactly the stale-extraction failure the wipe
invariant exists to prevent.

So extraction and composition live here, in a wrapper that is the single
documented way to run the suite:

    python run_acceptance.py                  # the effective spec (default)
    python run_acceptance.py --specs          # source of truth only, as-is
    python run_acceptance.py --lint           # extract, then lint the output
    python run_acceptance.py --print-locations  # show the resolved composition
    python run_acceptance.py --dry-run        # (passthrough) behave dry run

Anything not consumed here is passed straight through to behave.

environment.py refuses to run unless OPENSPEC_ACCEPTANCE is set, which this
wrapper sets. That tripwire turns "somebody ran plain `behave`" from a silent
stale-extraction run into a loud failure -- a hole the JS stack does not have,
since its config extracts unconditionally.

Stdlib only, 3.8+ compatible.
"""

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

from extract_gherkin import ExtractionError, extract_all  # noqa: E402
from openspec_effective_spec import (  # noqa: E402
    CompositionError,
    effective_locations,
    source_of_truth_locations,
)


def main(argv):
    # Resolve .extracted/, reports/ and the returned relative locations the way
    # the JS runner does -- from the suite root, wherever it was invoked from.
    os.chdir(HERE)

    specs_only = "--specs" in argv
    print_only = "--print-locations" in argv
    lint = "--lint" in argv
    passthrough = [a for a in argv if a not in ("--specs", "--print-locations", "--lint")]

    try:
        out_dir, written = extract_all()
    except ExtractionError as err:
        sys.stderr.write("[extract-gherkin] %s\n" % err)
        return 1
    sys.stderr.write(
        "[extract-gherkin] %d spec.md file(s) extracted to %s\n" % (len(written), out_dir)
    )

    if lint:
        # One linter for both stacks: gherkin-lint over the extracted output,
        # with the shared .gherkin-lintrc. Pass `.extracted` as a DIRECTORY
        # argument -- a quoted '**' glob silently matches nothing through the
        # dot-directory.
        return subprocess.call(["npx", "gherkin-lint", ".extracted"])

    try:
        locations = source_of_truth_locations() if specs_only else effective_locations()
    except CompositionError as err:
        sys.stderr.write("[effective-spec] %s\n" % err)
        return 1

    if print_only:
        for location in locations:
            print(location)
        return 0

    if not locations:
        sys.stderr.write("[effective-spec] no specs to run\n")
        return 1

    os.environ["OPENSPEC_ACCEPTANCE"] = "1"
    # Invoke behave through THIS interpreter (`-m behave`), not the `behave`
    # console script: execvp would search PATH, which breaks whenever the suite
    # is run with an unactivated venv's python (`.venv/bin/python
    # run_acceptance.py`). exec, so behave's exit code IS this process's.
    os.execv(sys.executable, [sys.executable, "-m", "behave"] + passthrough + locations)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
