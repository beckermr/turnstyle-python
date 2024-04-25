import sys
import os
import time
import subprocess

import github


def _parse_int(name, default):
    if name not in os.environ:
        return None
    try:
        return int(os.environ[name])
    except Exception:
        return default


def _parse_str(name, default):
    if name not in os.environ:
        return default

    name = os.environ.get(name, default)

    if name == "" or name.lower() == "none":
        return default


def _set_output(cmd):
    subprocess.run(
        'echo "force_continued=%s" >> "$GITHUB_OUTPUT"' % cmd,
        check=True,
        shell=True,
    )


# get inputs
workflow_name = _parse_str("WORKFLOW_NAME", os.environ["GITHUB_WORKFLOW"])
polling_interval = _parse_int("POLL_INTERVAL", 60)
continue_after = _parse_int("CONTINUE_AFTER", None)
abort_after = _parse_int("ABORT_AFTER", None)

print(" wfn:", os.environ.get("WORKFLOW_NAME"), flush=True)
print("ghwf:", os.environ.get("GITHUB_WORKFLOW"), flush=True)

print("computed workflow name '%s'" % workflow_name, flush=True)

if "GITHUB_HEAD_REF" in os.environ and len(os.environ["GITHUB_HEAD_REF"]) > 0:
    branch = os.environ["GITHUB_HEAD_REF"]
elif "GITHUB_REF" in os.environ and len(os.environ["GITHUB_REF"]) > 0:
    branch = os.environ["GITHUB_REF"][11:]
else:
    # TODO: should this be main?
    branch = "master"
print("computed branch '%s' for workflow" % branch, flush=True)

gh = github.Github(os.environ["GITHUB_TOKEN"])
repo = gh.get_repo(os.environ["GITHUB_REPOSITORY"])

wf = None
limit = 100
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
attempt = 0
while run is None and attempt < 10:
    try:
        limit = 100
        done = 0
        for _run in wf.get_runs():
            if (
                _run.status in ["in_progress"]
                and _run.id != int(os.environ["GITHUB_RUN_ID"])
                and _run.head_branch == branch
            ):
                run = _run
                break

            done += 1
            if done == limit:
                break
    except Exception as e:
        if attempt == 9:
            raise e

    attempt += 1

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
