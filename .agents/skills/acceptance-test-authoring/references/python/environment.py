"""behave hooks for the acceptance suite: boot the app, attach page objects.

Two things here are load-bearing beyond ordinary setup.

1. THE WRAPPER TRIPWIRE. behave parses the feature files before before_all
   fires, so extraction cannot live here (see run_acceptance.py). That leaves a
   hole the JS stack does not have: running plain `behave` would happily execute
   a stale .extracted/ tree. before_all refuses to start unless the wrapper set
   OPENSPEC_ACCEPTANCE, turning a silent wrong-result run into a loud failure.

2. PAGE OBJECTS ONLY. Step definitions must contain no selectors, URLs or
   regexes. `context` is the World: a thin HTTP client plus page-object
   instances. Parse responses with BeautifulSoup, never with regexes over raw
   HTML. See the skill's Page Object Model section.

This file must sit at the acceptance-tests/ root alongside steps/ -- behave
derives its base directory by walking UP from the first location argument until
it finds a steps/ directory, and loads environment.py from there.
"""

import os


def before_all(context):
    if not os.environ.get("OPENSPEC_ACCEPTANCE"):
        raise RuntimeError(
            "Run the suite via `python run_acceptance.py` (not plain `behave`).\n"
            "The wrapper extracts the Gherkin from openspec/**/spec.md and composes "
            "the effective spec; running behave directly would execute a stale or "
            "missing .extracted/ tree."
        )

    # TODO: boot the application under test and record its base URL, e.g.
    # context.app = start_app()
    # context.base_url = context.app.base_url


def after_all(context):
    # TODO: shut the application down.
    # if getattr(context, "app", None):
    #     context.app.stop()
    pass


def before_scenario(context, scenario):
    # TODO: reset per-scenario state and attach page objects, e.g.
    # context.client = HttpClient(context.base_url)
    # context.signup_page = SignupPage(context.client)
    pass
