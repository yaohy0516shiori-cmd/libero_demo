# LIBERO environment probes and a π0.5 closed loop through Armory

This repository contains three pieces of work on the [LIBERO](https://github.com/Lifelong-Robot-Learning/LIBERO) benchmark:

1. **Environment probes** (`libero_test/audit/`): what a LIBERO environment takes and returns, how an episode starts and ends, how simulated time advances, how long a scene takes to settle, what one control step costs, and whether the world can be changed mid-episode.
2. **Task inventory** (`libero_tasks/`): all 130 tasks, with a rendered frame, instruction and scene for each.
3. **Closed-loop demo** (`run_armory_demos.py`, `demo/`): the LeRobot π0.5 checkpoint fine-tuned for LIBERO, served through [Armory](https://github.com/GaTech-RL2/armory)'s own server, scheduler and client, with one robot and with four robots sharing one model, and per-stage timing throughout.

No SGLang, quantisation, model compilation, RTC or batching optimisation is used.

---

## Repository layout

```text
.
├── run_armory_demos.py        entry point: runs the N=1 and N=4 closed-loop conditions
├── demo/                      Armory server/client integration and the π0.5 runtime
├── analysis/                  log checks, summary tables, timing plots, wall-clock videos
├── tools/                     model download and warm-up observation capture
├── tests/                     unit tests for the demo code
├── assets/warmup/             one recorded LIBERO observation used to warm the model up
├── results/                   the closed-loop run (videos are not stored) and the GPU-rendering comparison
├── verification/              hardware, dependencies, checkpoint hash, standalone inference check
├── libero_test/audit/         environment probes and their results
├── libero_tasks/              task inventory: frames, contact sheets, task and scene lists
└── models/                    weights and tokenizer (not stored; see Setup)
```

---

## Setup

Tested on WSL2 Ubuntu 22.04 with an RTX 4060 Laptop GPU (8 GB), about 21 GiB of memory for WSL, PyTorch 2.7.1 + CUDA 12.6.

Two Python environments are used, so that the model stack and the simulation stack never share dependencies:

| Environment | Used for | Location |
|---|---|---|
| Armory's environment | LIBERO simulation, the Armory client, the environment probes | `$ARMORY_ROOT/.venv` |
| This repository's `.venv` | Model serving (LeRobot π0.5) and analysis | `./.venv` |

**1. Armory.** Clone [Armory](https://github.com/GaTech-RL2/armory) at commit `e876202ede99723f4be40d8d7cab31847bbd14a9` with its submodules and create its environment with the LIBERO dependencies, following Armory's own instructions. LIBERO comes from Armory's submodule `third_party/libero` (commit `65a492a`, libero 0.1.0). All scripts here find Armory through `ARMORY_ROOT`, which defaults to `/root/work/armory`:

```bash
export ARMORY_ROOT=/path/to/armory
```

**2. Model environment.** Python 3.11.16 with `lerobot==0.4.4`, `torch==2.7.1`, `torchvision==0.22.1` and `transformers` from LeRobot's adapted branch at commit `dcddb970176382c0fcf4521b0c0e6fc15894dfe0`. The full pinned list is in `verification/dependencies.txt`.

**3. Weights.** Download the checkpoint at its pinned revision and check its hash:

```bash
.venv/bin/python tools/download_model.py        # lerobot/pi05_libero_finetuned @ 8e17415...
sha256sum models/pi05_finetuned/model.safetensors
# 877b3ec1130548b69af7f8aeef3ec9d3fc7738040f0b9beb490857ec970997ae
```

**4. Tokenizer.** π0.5 uses the PaliGemma SentencePiece tokenizer from the public bucket that OpenPI uses:

```bash
curl -L https://storage.googleapis.com/big_vision/paligemma_tokenizer.model \
     -o models/paligemma_tokenizer.model
```

`models/tokenizer/` is generated from it when the model loads.

**5. Warm-up observation.** `assets/warmup/observation.npz` is included. To record it again (overwrites the existing one):

```bash
MUJOCO_GL=egl $ARMORY_ROOT/.venv/bin/python tools/capture_observation.py
```

---

## Running

**Closed-loop demo**

```bash
.venv/bin/python run_armory_demos.py --robots 1 4 --seconds 120
```

Each run writes a new `results/armory_<date>_<time>/` with `n1/` and `n4/`. Cameras are rendered on the CPU by default (`--renderer osmesa`) and the model runs on the GPU; `--renderer egl` renders on the GPU instead (see the results below for why that is not the default). N=4 means four independent LIBERO scenes sharing one model that serves one request at a time. It is not four model copies and not four arms in one scene.

**Analysis** (regenerates tables, timing plots and wall-clock videos inside a run; raw logs are never modified; needs the monotonic-clock fields introduced with this run, so it does not apply to the earlier GPU-rendering comparison):

```bash
.venv/bin/python analysis/analyze_armory.py results/armory_20260923_160823
```

**Tests**

```bash
.venv/bin/python -m unittest discover -s tests -v
```

**Environment probes**

```bash
cd libero_test/audit
MUJOCO_GL=egl $ARMORY_ROOT/.venv/bin/python main.py --section all --out results_x
```

| Section | Question it answers | Main outputs |
|---|---|---|
| `inspect` | Action semantics, observation fields and frames, reward/done/success, time model, how Armory preprocesses and serialises observations | `report.json`, first frames |
| `settle` | How long the stored initial states take to come to rest | `settling_summary.md` / `.csv`, `steps/*.csv` |
| `timing` | Cost of one step (physics, rendering, total) and whether a paced loop keeps up with real time | `timing_*.csv`, `paced_256.csv`, `time_alignment.png` |
| `dynamic` | Whether forces and pose edits can be applied mid-episode | `*_trajectory.csv`, before/after frames |

Useful options: `--suite`, `--task`, `--init`, `--only-task`, `--all-tasks` (all 130 tasks), `--steps`, `--max-wait` / `--window` (settling criterion), `--init-count`. Without `--out` nothing is written. `check_render_wait.py` measures how far objects move between step 10 and step 30.

In each `report.json`, fields are configuration (`versions`, `args`, `criteria`), provenance (`source`, `semantics_source`: file, line and code), checks (`PASS` or booleans) or measurements (usually `{mean, p50, p95, max}`). CSV files hold the per-step raw data.

---

## How the closed loop is wired

```text
run_armory_demos.py
├── demo/armory_server.py → Armory PolicyServer / scheduler / GPU worker
│   └── demo/armory_backend.py → demo/model_runtime.py → LeRobot π0.5
│       ├── demo/load_helpers.py
│       └── models/pi05_finetuned/, models/tokenizer/
└── demo/armory_client_demo.py → Armory runner / PolicyAgent / ActionChunkBroker
    └── LIBERO → robosuite → MuJoCo
```

| File | Role |
|---|---|
| `run_armory_demos.py` | Starts N=1 and N=4, manages processes, rendering backend, output folders and GPU sampling |
| `demo/armory_server.py` | Configures and starts Armory's unmodified model server |
| `demo/armory_client_demo.py` | Reuses Armory's robot runner; adds timing, reply logging and video |
| `demo/armory_backend.py` | Turns Armory observations into model inputs and returns action chunks |
| `demo/model_runtime.py` | Loads the real weights; preprocessing, inference, postprocessing; per-stage timing |
| `demo/load_helpers.py` | Restores non-persistent model buffers the way the upstream code initialises them |
| `analysis/analyze_armory.py` | Checks logs, writes CSV summaries, timing plots and wall-clock videos |

The model server and the robots run in parallel. While the model computes, each robot keeps stepping on the actions it has buffered (20 Hz is the target; the demo below reached 3–4 steps per second). Once the buffer is empty the robot receives a null action (no arm motion, gripper command unchanged) and the simulation keeps advancing. Each reply is a chunk of 50 actions; at most 10 are executed before a newer chunk replaces it.

Weights are loaded with strict key and shape checks; the tied embedding and the non-persistent buffers are restored explicitly, and there is no fallback to random parameters. Inference runs in native BF16 with selected FP32 parameters.

---

## Results

### LIBERO environment (`libero_test/audit/`)

These probes call LIBERO directly, without Armory's loop and without a model, using idle actions unless stated otherwise.

**Interface.** One call to `env.step(action)` advances one control step and returns `obs, reward, done, info`.

| | |
|---|---|
| Action | 7 values in [−1, 1]: end-effector translation delta (3), rotation delta as axis-angle (3), gripper (+1 close, −1 open, 0 keep). The OSC_POSE controller scales them to a target increment of at most ±0.05 m / ±0.5 rad per step |
| Observation | 44 fields for libero_10 task 0 (8 objects; the count grows with the number of objects): two cameras, joint and end-effector state, gripper, per-object poses, and two concatenated vectors of the same values. Positions are in the world frame, quaternions in x, y, z, w order |
| reward / done | reward is 1 once the BDDL goal holds, else 0. The `done` returned by LIBERO's `step()` means success; reaching the step limit is a separate internal flag |
| Before an episode | Task (BDDL file), environment configuration, and one of 50 stored initial states per task |

**Time.** Only `step()` advances simulated time: 25 physics substeps of 2 ms, i.e. 0.05 s per control step at 20 Hz. The step limit is 1000 control steps (50 s). Whether the scene keeps moving while a model computes depends on the loop that calls `step()`: LIBERO's own evaluation waits for the model, Armory does not.

**Settling** (`results_all_tasks/`, all 130 tasks, initial state 0). The stored initial states are not at rest: objects start up to 29 mm inside the table (resolved in one physics step) and some start in mid-air.

| Control step at which | Min | Median | 95th pct. | Max |
|---|---:|---:|---:|---:|
| the scene first becomes quiet | 5 | 13 | 21 | 29 |
| 20 consecutive quiet steps confirm it | 24 | 32 | 40 | 48 |

LIBERO's evaluation waits 5 steps and Armory waits 10. At step 10, 25 of 130 tasks are quiet; at step 30 all are. In 17 tasks objects are still above the camera frame at step 10 (`results_render_check/`).

**Cost of one step** (`results_time/`, one environment, libero_10 task 0, 100 steps, mean / 95th percentile, budget 50 ms):

| | No cameras | 128×128, two cameras | 256×256, two cameras |
|---|---|---|---|
| Physics (25 substeps) | 1.6 / 1.8 ms | 1.5 / 1.8 ms | 2.0 / 3.3 ms |
| Rendering | 0 | 13.8 / 19.0 ms | 24.9 / 37.4 ms |
| Full step | 7.4 / 8.5 ms | 21.2 / 27.3 ms | 35.0 / 52.8 ms |

Paced to 20 Hz at 256×256, 31 of 100 steps exceeded 50 ms; because deadlines are fixed in advance the lag carried over, reaching about 290 ms, and 66 steps finished late. These numbers come from a laptop under WSL, where EGL is translated to Direct3D.

**Disturbance** (`results_dynamic/`). Both an external force and a direct pose edit take effect mid-episode; the pose edit does not advance simulated time. This is a single-case feasibility check with no policy running.

### Task inventory (`libero_tasks/`)

130 tasks in 5 suites over 22 scene definitions (20 named kitchen, living-room and study scenes plus the two generic setups used by libero_spatial and libero_object). Frames are rendered at 256×256 after 30 settle steps, agent view on the left and wrist camera on the right.

| File | Content |
|---|---|
| `LIBERO_tasks.md` | Task list by suite, with scene and instruction |
| `tasks.json`, `scenes.json` | Task records; the same tasks grouped by scene |
| `img/` | One frame per task |
| `sheet_*.png` | Contact sheets per suite |
| `scene_gallery.png` | One agent-view frame per scene, with the number of tasks that reuse it |
| `render_libero_tasks.py`, `rerender.sh` | Render `img/` and `tasks.json` (30 settle steps) |
| `make_sheets.py` | Build `sheet_*.png` and `LIBERO_tasks.md` |
| `make_scene_gallery.py` | Build `scenes.json` and `scene_gallery.png` |

The scripts run in Armory's environment and read and write their own folder by default. To regenerate everything:

```bash
cd libero_tasks
bash rerender.sh                                  # restarts itself after the occasional SIGFPE crash
$ARMORY_ROOT/.venv/bin/python make_sheets.py
$ARMORY_ROOT/.venv/bin/python make_scene_gallery.py
```

Frames that already exist are skipped, so delete `img/` first to render from scratch.

### Closed-loop demo (`results/armory_20260923_160823/`)

LIBERO-Spatial, four layouts of "put the black bowl on the plate"; the single robot ran the bowl-on-the-ramekin layout, and each of the four robots ran a different layout. 120 s of real time per condition, episodes capped at 280 steps, two 256×256 cameras rendered on the CPU, one request served at a time.

| | Successful | Failed at the step limit | Cut off at 120 s |
|---|---:|---:|---:|
| 1 robot | 1 | 1 | 1 |
| 4 robots | 6 | 1 | 4 |

Seven of the nine episodes that ran to completion succeeded, in 94–122 steps. In both failures the bowl reached the plate but ended up tilted on its rim, and the robot kept adjusting until the step limit (from the recordings; final object poses were not checked). LeRobot reports 97.0% on LIBERO-Spatial for this exact checkpoint (`pi05_libero_finetuned_v044` is at the same revision with the same weights hash), measured with its own evaluation, in which the simulation waits for the model. With 14 episodes on 4 of 130 tasks this is not a success rate, and the gap is not explained. Candidates are the asynchronous loop acting on older observations, a preprocessing difference on the Armory path, and scenes still settling: at initial state 0 the four layouts need 10, 21, 22 and 29 steps to come to rest, while Armory waits 10 steps plus 2–9 null-action steps for the first chunk. Separating them takes three comparisons on the same tasks and initial states: LeRobot's own evaluation, the Armory path made to wait for the model, and the Armory loop with a 10- versus 30-step settle.

**Where the time goes, per control step and robot**

| | 1 robot | 4 robots |
|---|---|---|
| `env.step`, cameras on the CPU | 159 ms | 188–196 ms |
| Extra 512×512 frame for the demo video | 97 ms | 119–121 ms |
| Resulting speed | about 4 steps/s | about 3 steps/s |
| Model call (runs in parallel in the server) | 0.53 s | 0.52–0.54 s |
| Gap between new action chunks for one robot | 0.54 s | 2.2 s |

The video frame alone adds about 40% to every step. Even without it, 159 ms per step is three times the 50 ms budget.

**Latency on two clocks.** From the moment the observation the server picked was ready to the moment the robot received the reply took 0.69 s (1 robot) and 0.77 s (4 robots): 0.15 / 0.24 s waiting while the model served an earlier request, 0.54 / 0.53 s for the model call, about 1 ms to send the reply back. Yet a robot only fell about 3 control steps (0.15 s of simulated time) behind its observation: the scene kept stepping, but each step took 260–310 ms of real time, so the simulation ran 5.4× (1 robot) and 6.5× (4 robots) slower than real time. At a true 20 Hz the same delay would be about 14 and 15 steps. Real-time numbers here describe this laptop; step counts understate what a 20 Hz robot would experience.

All durations use the monotonic clock (`*_mono_s` fields). The system clock of this WSL machine stepped back by about 1.1 s roughly every half minute during the run, so the `timestamp`, `request_timestamp` and `response_timestamp` fields written by Armory should not be used for durations.

**Starvation.** Not counting the wait for the first chunk, a robot never ran out of actions with 1 robot (0 of 439 steps), and did on 6–20 of about 350 steps per robot with 4 robots. Given the slowed simulation these counts do not carry over to a 20 Hz loop.

**Rendering on the GPU next to the model** (`results/gpu_rendering_comparison/`). Free GPU memory fell to 13–28 MiB and a model call took 9–14 s with one robot; with four robots the first call took 142 s. Moving rendering to the CPU brought the model call back to about 0.5 s. Running simulation and model on the same machine therefore prevents 20 Hz either way.

A standalone check of the model outside the loop is in `verification/pi05_real_inference.json`: 1.51 s for the first call and 0.46 s for the second, producing finite 50×7 action chunks, with about 7.3 GB of GPU memory allocated at peak.

**Files in a run** (robot indices start at 0):

| File | Content |
|---|---|
| `run.json` | Model, configuration and versions for the run |
| `COMPLETE` | The run finished (not that tasks succeeded) |
| `comparison.csv`, `outcomes.json` | Per-robot timing and task outcomes |
| `delivered_requests.csv` | Model calls matched to delivered replies |
| `validation.json` | Consistency checks on the raw records |
| `n*/client/results.csv` | Per episode: success, cut-off, steps, hold steps |
| `n*/client/<robot>/<episode>/` | `metadata.json`, `steps.parquet`, `action_chunks.parquet` |
| `n*/client/demo_trace/robot_N/` | Per-step timing (`stages.csv`, `stages.jsonl`) and reply times (`responses.jsonl`) |
| `n*/serve/server/` | Model stage timings (`model_stages.jsonl`), model and server metadata, Armory events, batches and scheduler decisions |
| `n*/model_stages.csv` | Model calls without warm-up |
| `n*/gpu.csv` | GPU memory and utilisation |
| `n*/client.log`, `n*/server.log`, `n*/client/run.log` | Logs |
| `n*/client/plots/` | Armory's built-in plots |
| `n*/timing.png` | Per-stage timing and execution timeline |
| `n*/*_preview.png`, `n*/*.json` | Previews and playback notes for the wall-clock videos (videos themselves are not stored) |

`results/gpu_rendering_comparison/` keeps only the configuration (`run.json`) and the measured contention (`contention_evidence.json`: model-call times, GPU memory, episodes) of the earlier run with cameras rendered on the GPU.

Absolute paths inside raw logs are the paths at recording time and were not rewritten.

---

## Verification (`verification/`)

| File | Content |
|---|---|
| `hardware.json`, `dependencies.txt`, `transformers_revision.txt` | Hardware and exact package versions |
| `checkpoint_sha256.txt`, `pi05_finetuned_header.json` | Checkpoint hash and parameter metadata |
| `preprocessing_verified.txt` | Check of the input preprocessing against the official pipeline |
| `pi05_real_inference.json`, `real_inference.log`, `smoke_actions.npy` | Standalone real-weight inference, 2026-09-23 |

---

## Limitations

- On this 8 GB laptop π0.5 runs only with CPU rendering and far below 20 Hz; representative inference times need a server GPU. Armory's own latency profile for the same model is 73 ms per call on an L40S.
- How many environments one simulation host can step at 20 Hz, without a model on it, has not been measured.
- Long runs (many resets over tens of minutes) are untested; repeatedly creating LIBERO environments in one process occasionally crashes it (SIGFPE).
- Settling covers all 130 tasks at initial state 0 only; the interface, timing and disturbance probes used one task; the demo covers four LIBERO-Spatial layouts for 120 s.
- The demo validates LeRobot π0.5 through Armory, not this checkpoint through SGLang.

---

## Sources and licences

- LIBERO: <https://github.com/Lifelong-Robot-Learning/LIBERO>
- Armory: <https://github.com/GaTech-RL2/armory>
- π0.5 LIBERO checkpoint: <https://huggingface.co/lerobot/pi05_libero_finetuned>
- LeRobot π0.5: <https://huggingface.co/docs/lerobot/en/pi05>
- OpenPI (tokenizer source, model requirements): <https://github.com/Physical-Intelligence/openpi>

Model weights and the tokenizer are not redistributed here; their use is governed by the licences of the respective upstream projects.
