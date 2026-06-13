![gds](../../workflows/gds/badge.svg)

# tt_um_tapewright_pwm — TapeWright's first Tiny Tapeout tile

An 8-bit PWM peripheral on the [Tiny Tapeout](https://tinytapeout.com) tile
interface — the first silicon target driven through
[**TapeWright**](https://github.com/gchen19/TapeWright) (an agent/MCP harness over
the open LibreLane / OpenROAD flow). This repo is the Tiny Tapeout submission
project: RTL + metadata + tests, with the `tt-gds-action` signoff gate wired to run
on a **local self-hosted runner**.

- 📄 Design docs: [docs/info.md](docs/info.md)
- 🔬 Live datasheet / GDS viewer: https://gchen19.github.io/my-tt-pwm/

---

## 1. The design

A free-running 8-bit counter increments every clock. The output `pwm_out` is high
while `counter < ui_in`, so over each 256-cycle period the duty cycle equals
`ui_in / 256`. It's fully digital, deterministic, and fits a single 1×1 TT tile.

```
        ui_in[7:0]  (duty setpoint)
             │
   counter ──┤  pwm_out = (counter < ui_in)   ──►  uo_out[0]
   (8-bit) ──┘  counter[7:1]                  ──►  uo_out[7:1]   (scope taps)
```

| Bus | Bit | Function |
|---|---|---|
| `ui_in`  | [7:0] | duty-cycle setpoint (0–255) |
| `uo_out` | 0     | `pwm_out` |
| `uo_out` | [7:1] | `counter[7:1]` (observation) |
| `uio_*`  | —     | unused (driven 0, all inputs) |

RTL: [`src/tt_um_tapewright_pwm.v`](src/tt_um_tapewright_pwm.v). Clock 50 MHz
(`CLOCK_PERIOD: 20` in [`src/config.json`](src/config.json)); the design has ample
timing headroom for this shallow logic.

## 2. How it's verified & hardened — the Tiny Tapeout gate

Every push runs [`.github/workflows/gds.yaml`](.github/workflows/gds.yaml), which
invokes `TinyTapeout/tt-gds-action@ttsky26c` (`sky130A`). A green run is the real
shuttle acceptance check — the same suite a paid shuttle runs, for free in CI:

| Job | What it does |
|---|---|
| **`gds`** | Hardens the RTL → GDSII with LibreLane (Yosys → OpenROAD → Magic/KLayout), then **DRC + LVS** |
| **`precheck`** | Tiny Tapeout pinout / metadata / design-rule checks |
| **`gl_test`** | **Gate-level** cocotb sim: re-runs the duty-cycle test against the *hardened netlist* (Icarus) |
| **`viewer`** | Renders a GDS viewer + datasheet and publishes it to GitHub Pages |

The harden config and `info.yaml` were prepared by TapeWright; the gate-level
testbench ([`test/tb.v`](test/tb.v), [`test/test.py`](test/test.py),
[`test/Makefile`](test/Makefile)) drives the design through the standard TT pins so
the *same* test passes on both RTL and the post-layout netlist.

## 3. CI architecture: hybrid self-hosted + GitHub-hosted

The gate runs on a **self-hosted GitHub Actions runner on a local workstation**, so
the heavy silicon work executes on local hardware. One job is the exception:

| Job | Runs on | Why |
|---|---|---|
| `gds` | **self-hosted** (`my-tt-pwm-local`) | LibreLane harden in a Docker container |
| `gl_test` | **self-hosted** | iverilog + cocotb gate-level sim |
| `viewer` | **self-hosted** | GDS render + Pages deploy |
| `precheck` | **GitHub-hosted** (`ubuntu-24.04`) | see below |

**Why `precheck` is GitHub-hosted.** `precheck` installs its own (single-user) nix
via `nix-build`/`nix-shell`. On this workstation there is already a **root-owned
multi-user nix** (for an unrelated LibreLane toolchain), and the action can't
`chmod` it — so its install fails. Running `precheck` inside a container was tried
and proved fragile (bare `ubuntu:24.04` lacks `jq`; the `catthehacker/act` image
disables pip cache and breaks `setup-python`'s `cache: pip`; `nix-build`'s sandbox
needs user namespaces; and a root container leaves root-owned files in the shared
`_work`, breaking later host-side jobs). Since `precheck` is a lightweight,
image-sensitive check, it runs on GitHub's clean image where it's designed to run,
while the heavy jobs stay local.

### The self-hosted runner setup

The runner is a systemd service so it survives reboots and matches the box's other
runners:

```bash
# 1. Register a runner from the repo's Settings → Actions → Runners token:
cd ~/actions-runner-my-tt-pwm
./config.sh --url https://github.com/gchen19/my-tt-pwm --token <REG_TOKEN> \
  --name my-tt-pwm-local --labels self-hosted --unattended

# 2. Install + start it as a service:
sudo ./svc.sh install $USER && sudo ./svc.sh start
```

Two host prerequisites the GitHub-hosted image provides but a bare machine doesn't:

```bash
# LibreLane runs the EDA tools in a container — the runner needs Docker:
sudo apt-get install -y docker.io
sudo usermod -aG docker $USER      # then restart the runner so it inherits the group

# gl_test/precheck install the PDK to a hardcoded path; make it writable:
sudo mkdir -p /home/runner/pdk && sudo chown -R $USER /home/runner
```

The workflow targets the runner via `runs-on: self-hosted` on the three local jobs
(`precheck` stays `runs-on: ubuntu-24.04`).

## 4. Run it yourself

- **Trigger the gate:** push to `main` (or use the Actions tab → *gds* →
  *Run workflow*). Watch with `gh run watch` or the Actions tab.
- **Build locally without CI:** see Tiny Tapeout's
  [local hardening guide](https://www.tinytapeout.com/guides/local-hardening/), or
  drive it through TapeWright (`tapewright harden …`).
- **Run the test locally** (cocotb):

  ```bash
  cd test
  make            # RTL sim (Icarus)
  make GATES=yes  # gate-level sim against the hardened netlist (needs gate_level_netlist.v)
  ```

## 5. Status

The gate runs **green** — `gds` + `gl_test` + `viewer` on the local runner,
`precheck` on GitHub-hosted. See the latest run under
[Actions](https://github.com/gchen19/my-tt-pwm/actions) and the published datasheet
at https://gchen19.github.io/my-tt-pwm/.

**Optional next step:** submit to a physical shuttle by committing the design in the
[Tiny Tapeout app](https://app.tinytapeout.com/) before the **TTSKY26c** deadline
(~2026-09-07; re-confirm on tinytapeout.com).

## Resources

- [TapeWright](https://github.com/gchen19/TapeWright) — the harness that drove this design
- [Tiny Tapeout FAQ](https://tinytapeout.com/faq/) · [LibreLane](https://librelane.readthedocs.io/)
- [Self-hosted runners](https://docs.github.com/en/actions/hosting-your-own-runners)
