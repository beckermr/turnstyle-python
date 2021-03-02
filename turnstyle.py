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

if "GITHUB_HEAD_REF" in os.environ:
    branch = os.environ["GITHUB_HEAD_REF"]
elif "GITHUB_REF" in os.environ:
    print(os.environ["GITHUB_REF"])
    branch = os.environ["GITHUB_REF"][11:]
else:
    # TODO: should this be main?
    branch = "master"
print("computed branch '%s' for workflow" % branch, flush=True)

gh = github.Github(os.environ["GITHUB_TOKEN"])
repo = gh.get_repo(os.environ["GITHUB_REPOSITORY"])

wf = None
limit = 500
done = 0
for _wf in repo.get_workflows():
    if _wf.name == workflow_name:
        wf = _wf
        break

    done += 1
    if done == limit:
        break

if wf is None:
    print("No workflow with name '%s' found! Continuing!" % workflow_name, flush=True)
    _set_output("")
    sys.exit(0)

run = None
limit = 500
done = 0
for _run in wf.get_runs(branch=branch):
    if _run.status in ["in_progress"] and _run.id != int(os.environ["GITHUB_RUN_ID"]):
        run = _run
        break

    done += 1
    if done == limit:
        break

if run is None:
    print("No running workflows found! Continuing!", flush=True)
    _set_output("")
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
