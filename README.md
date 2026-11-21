# WebOS services

This repository holds the user-level Linux units and launchers for WebOS GPU compute. Application source and model weights have independent lifecycles.

| Service | Runs on | What it starts | WebOS consumer |
|---|---|---|---|
| webos-gpu-monitor.service | GPU machines | A local sampler for GPU utilization, VRAM and identifiable model processes | GPU Monitor under System Tools |
| [`webos-model@PROFILE.service`](units/webos-model@.service) | A machine with that local profile installed | The inference command specified by the operator | Image Studio for image rendering. Text and 3D clients need matching queue routes. |
| Existing PCC and Strata units | Hosts that already provide them | Their own model runtimes and settings | Eligible for routing after worker qualification |

Clone the repository and run `python3 install.py` from the checkout as the service user. This installs the units in the user systemd manager. Start telemetry with `systemctl --user enable --now webos-gpu-monitor.service`. Use `systemctl --user status webos-gpu-monitor.service` to check it. The sampler replaces its latest record in the user runtime directory. It keeps no series or history.

## GPU Monitor

The signed-in GPU Monitor shows the samples supplied by these services and queue totals from the WebOS coordinator. Its browser review includes the four-host view and screenshots at phone, tablet, 1080p and 4K sizes. [GPU Monitor screenshots and review](https://github.com/CC-David-CC/gpu-monitor#browser-review)

## Model profiles

Create a private file at `~/.config/webos-services/models/example.json` with an absolute executable and arguments, for example:

```json
{"argv":["/opt/llama/bin/llama-server","--model","/mnt/models/example.gguf","--host","127.0.0.1","--port","18190"],"model":"example","precision":"Q4_K_M"}
```

Use `systemctl --user start webos-model@example`, `stop`, `restart`, or `status`. The optional `cwd` field sets the working directory. Model identifiers and quantization labels describe the selected weights. Keep model paths, private credentials, checkpoints and deployment profiles on the machine. Stopping a busy service can interrupt its job. Confirm the running request has finished before a planned model swap. A disconnected worker with an uncertain job requires operator reconciliation before reassignment.

The image adapter uses an owner-only Unix socket and the independently installed Image Studio renderer. Its profile invokes `bin/image-worker serve /absolute/venv/bin/python /absolute/render.py` with Python. The gateway invokes the adapter's `submit` command. Runtime operations stay on the operator machine. Browser clients submit signed jobs to WebOS.

The WebOS parent also owns the viewer backend packaging and the test-account maintenance timer. Their source lives in the parent under `deploy/`. Existing host-specific PCC and Strata installations remain independently managed.

## Recovering an interrupted remote job

On the coordinator, `bin/reconcile-job /path/to/compute-jobs.sqlite3` lists indeterminate job IDs. Check whether execution has actually stopped on the worker first. Once verified, add `--confirm-stopped JOB` to mark that job failed and release its account and worker slots. The scheduler picks up the next waiting job. A queued or running job cannot be cleared with this command.
