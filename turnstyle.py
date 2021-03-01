import sys
import os
import time

import github


def _parse_int(name, default):
    if name not in os.environ:
        return None
    try:
        return int(os.environ[name])
    except Exception:
        return default


def _set_output(cmd):
    print("::set-output name=force_continued::%s" % cmd, flush=True)


# get inputs
workflow_name = os.environ["GITHUB_WORKFLOW"]
polling_interval = _parse_int("INPUT_POLL-INTERVAL-SECONDS", 60)
continue_after = _parse_int("INPUT_CONTINUE-AFTER-SECONDS", 10)
abort_after = _parse_int("INPUT_ABORT-AFTER-SECONDS", 10)

gh = github.Github(os.environ["GITHUB_TOKEN"])
repo = gh.get_repo(os.environ["GITHUB_REPOSITORY"])

wf = None
for _wf in repo.get_workflows():
    if _wf.name == workflow_name:
        wf = _wf

if wf is None:
    sys.exit(0)

run = None
for _run in wf.get_runs():
    if _run.status == "in_progress" and _run.id != os.environ["GITHUB_RUN_ID"]:
        run = _run

if run is None:
    sys.exit(0)

print("waiting on workflow run %s..." % run.id, flush=True)

start = time.time()
while True:
    dt = time.time() - start
    if (
        continue_after is not None
        and dt > continue_after
    ):
        _set_output("1")
        print("continuing after %d seconds" % dt, flush=True)
        sys.exit(0)

    if (
        abort_after is not None
        and dt > abort_after
    ):
        _set_output("")
        print("aborting after %d seconds" % dt, flush=True)
        sys.exit(1)

    if run.status == "completed":
        print("wrokflow run %s finished after %d seconds" % (run.id, dt), flush=True)
        _set_output("")
        sys.exit(0)

    time.sleep(polling_interval)
    run = repo.get_workflow_run(run.id)
