# momo Web Automation Testing Framework (Senior SDET)

This repository provides a professional-grade web automation framework skeleton built using **Python + Pytest + Playwright** targeting the search feature of the **momo shopping site** (`https://www.momoshop.com.tw/`).

It incorporates the Page Object Model (POM) pattern, custom CLI options for Headless and Debug modes, Git branching strategies, structured **`[PERF]`** performance logging, **retry-with-backoff** resilience against rate-limiting, and **third-party network filtering** to keep tests focused on the search feature.

---

## 1. Environment & Setup

This project is managed with **`uv`**, an extremely fast Python package and project
manager written in Rust. Dependencies are declared in **`pyproject.toml`** and pinned
in **`uv.lock`**; `uv` provisions the right Python version and the virtual environment
for you, so the steps below are all you need.

### Prerequisites
- `uv` installed:
  ```bash
  # macOS (Homebrew)
  brew install uv
  # or, any platform
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
  (You do **not** need to install Python yourself — `uv` will fetch the version pinned in `pyproject.toml`.)

### Installation Steps
1. **Install all dependencies** (creates `.venv` and installs the locked versions):
   ```bash
   uv sync
   ```
2. **Install the Playwright browser** (Chromium):
   ```bash
   uv run playwright install chromium
   ```
3. **(Recommended) Enable the git hooks** that keep `uv.lock` / `requirements.txt`
   in sync with `pyproject.toml` automatically on every commit:
   ```bash
   uv run pre-commit install
   ```

That's it — the environment is ready.

### Running Everything
All commands are run through `uv run` (no manual `source .venv/bin/activate` needed;
`uv` uses the project's `.venv` automatically):

```bash
# 1. Framework self-tests (unit/integration tests for the framework itself) — should be 40 passed
uv run pytest test/

# 2. The full E2E suite against the momo site (all SEARCH scenarios)
uv run python run_tests.py

# 3. A single smoke test (fast sanity check that the whole pipeline works)
uv run python run_tests.py -c SEARCH-001
```

> **Dependency management:** add/remove packages with `uv add <pkg>` / `uv remove <pkg>`
> (never edit `requirements.txt` by hand). `requirements.txt` is **auto-generated** from
> `uv.lock` by the `pre-commit` hook (`uv export`) and is kept only as a fallback for
> environments without `uv`.

---

## 2. Global Configuration & CLI Interface (`run_tests.py`)

The framework relies on a global configuration file **`config.ini`** for default execution settings. You can override these defaults directly from the CLI.

### Global Configuration (`config.ini`)
The default settings inside `config.ini` control the framework's baseline behavior:

| Parameter | Default Value | Allowed Values | Description / Behavior |
| :--- | :--- | :--- | :--- |
| `headless` | `true` | `true`, `false` | Run tests in headless (background) or headed (visible browser) mode. |
| `log_level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Logging verbosity. Setting to `DEBUG` triggers verbose outputs, 800ms action delay (`slow_mo`), and automatic video capture for all test cases. |
| `report_dir` | `./results` | Path string (relative/absolute) | Output directory for execution assets (HTML report, per-case logs/traces/videos). Path is auto-created if missing. |
| `pwdebug` | `false` | `true`, `false` | Enable Playwright Inspector interactive debugging GUI. Setting to `true` pauses execution at the start of tests (forces headed mode). |
| `trace` | `true` | `true`, `false` | Capture a Playwright execution trace (`.zip`) for every test case. |

### CLI Overrides
The `run_tests.py` wrapper accepts arguments to override the values inside `config.ini` dynamically, filter tests by level or ID, and control debugging outputs:

| CLI Options | Type / Format | Default (from `config.ini`) | Description / Override Behavior |
| :--- | :--- | :--- | :--- |
| `--headless`<br>`--headed` | Flag | `headless = true` | Overrides the browser mode. `--headless` runs in background; `--headed` opens a visible browser window. |
| `--log-level <LEVEL>`<br>`-l <LEVEL>` | Choice: `DEBUG`, `INFO`, `WARNING`, `ERROR` | `log_level = INFO` | Overrides logging level. `DEBUG` automatically activates verbose logger, slows execution by 800ms, and captures traces + videos. |
| `--report <DIR>`<br>`-r <DIR>` | Path | `report_dir = ./results` | Overrides the output directory for reports and assets. (Report filename is configured in `pytest.ini`). |
| `--pwdebug`<br>`--no-pwdebug` | Flag | `pwdebug = false` | `--pwdebug` enables Playwright Inspector GUI and pauses execution at start (forces headed mode). `--no-pwdebug` disables it. |
| `--trace`<br>`--no-trace` | Flag | `trace = true` | `--trace` forces trace capture (`.zip`) for every test case; `--no-trace` disables trace capture. |
| `--tier <TIERS>`<br>`-t <TIERS>` | Comma-separated list | None | Filter tests by tier markers: `RAT` (smoke/acceptance), `FAST` (happy path), `TOFT` (functionality), or `FET` (edge/negative paths). |
| `--test-case <IDS>`<br>`-c <IDS>` | Range / Comma-separated list | None | Filter tests by ID, e.g. `SEARCH-001`, a range `SEARCH-{001..003}`, or custom list `SEARCH-001,SEARCH-004`. |
| `--suite <NAMES>` | Comma-separated list | None | Run all test cases under the named suite(s), e.g. `SEARCH` -> `suites/SEARCH/`. Case-insensitive. Composes with `--tier` / `--test-case` (which filter within the selected suite). Errors and lists available suites if a name is unknown. |
| `--reruns <N>` | Integer | `0` (off) | Rerun each **failing** test up to `N` times (any failure, incl. `AssertionError`). Opt-in safety net for transient/throttle flakes. Rerun-rescued cases are flagged in the HTML report so flakiness stays visible (never silently masked). |
| `--reruns-delay <SECONDS>` | Integer | `5` | Seconds to wait before each rerun, so a momo rate-limit window can pass. Only applies when `--reruns > 0`. |

### CLI Examples
All commands are run through `uv run` (the project's `.venv` is used automatically — no manual activation needed).

```bash
# Run with defaults from config.ini (Headless, INFO log level)
uv run python run_tests.py

# Run in headed mode with verbose DEBUG logs (captures video/traces)
uv run python run_tests.py --headed -l DEBUG

# Run in headless mode with ERROR level logs, writing the report + assets under ./custom_results/
uv run python run_tests.py --headless -l ERROR -r ./custom_results

# Run tests and open the interactive Playwright Inspector GUI
uv run python run_tests.py --pwdebug
```

### Interactive Debugging (Playwright Inspector)
Playwright provides an interactive GUI debugging tool called the **Playwright Inspector**, which allows you to step through your test code line-by-line, inspect page elements, generate selectors, and audit actions.

#### Method 1: Global Debugging (via Environment Variable)
To pause execution at the very beginning of the test suite and step through all tests:
```bash
# macOS/Linux
PWDEBUG=1 uv run python run_tests.py
```
*When `PWDEBUG=1` is set: browser execution automatically switches to headed mode, timeouts are set to infinity, and the Playwright Inspector GUI opens alongside the browser window.*

#### Method 2: Target Debugging (via `page.pause()`)
To debug a specific step inside your test case or Page Object:
1. Insert `page.pause()` (or `self.page.pause()` inside POM classes) at the target line:
   ```python
   def test_happy_path_search(home_page, search_results_page):
       home_page.navigate()
       home_page.page.pause() # Execution pauses here, opening the Playwright Inspector!
       home_page.search_for("iPhone")
   ```
2. Run tests in **headed** mode:
   ```bash
   uv run python run_tests.py --headed
   ```

### Test Classification & Filtering (`--tier` / `-t`)
The framework classifies tests into distinct execution tiers to optimize build validation speed:
- **RAT (Release Acceptance Testing)**: Smoke test verifying that core search works (basic keyword search returns results).
- **FAST (Core Happy Paths)**: Essential happy path validations protecting core user experience flows.
- **TOFT & FET (Functional Toleration & Edge Testing)**: Comprehensive coverage including filtering, sorting, autocomplete and negative edge paths.

You can filter runs using the `--tier` (`-t`) argument (comma-separated list):
```bash
# Run only RAT (smoke) tests
uv run python run_tests.py --tier RAT

# Run both RAT and FAST tests together
uv run python run_tests.py -t RAT,FAST

# Run TOFT and FET tests
uv run python run_tests.py -t TOFT,FET
```

### Test Case ID Filtering (`--test-case` / `-c`)
The framework structures test cases into logical **Test Suites** (e.g. `SEARCH`) and assigns unique alphanumeric IDs (e.g. `SEARCH-001`). You can target specific test IDs or range patterns:
- **Single ID**: Runs a specific test case (e.g., `SEARCH-001`).
- **List of IDs**: Comma-separated list (e.g., `SEARCH-001,SEARCH-003`).
- **Range / Brace Expansion**: Supports range matching from start to end (e.g., `SEARCH-{001..003}` will execute `SEARCH-001`, `SEARCH-002`, and `SEARCH-003`).

```bash
# Run a single test case
uv run python run_tests.py --test-case SEARCH-001
# or short flag
uv run python run_tests.py -c SEARCH-001

# Run a range of test cases (e.g., SEARCH-001 to SEARCH-003)
uv run python run_tests.py -c "SEARCH-{001..003}"

# Run a custom comma-separated list of test cases
uv run python run_tests.py -c SEARCH-001,SEARCH-004
```

### Suite Filtering (`--suite`)
Run every test case under a whole suite by name (case-insensitive). Composes with `--tier` / `--test-case`.
```bash
# Run all cases in the SEARCH suite
uv run python run_tests.py --suite SEARCH

# Run only the RAT-tier case within the SEARCH suite
uv run python run_tests.py --suite SEARCH --tier rat

# Multiple suites (comma-separated)
uv run python run_tests.py --suite SEARCH,CART
```

### Custom Test Targeting & Reports
You can target specific test files or specify a custom report output directory:
```bash
# Run only a specific test class/case
uv run python run_tests.py suites/SEARCH/test_search.py::TestMomoSearch::test_happy_path_search

# Output report + assets to a custom directory
uv run python run_tests.py -r ./debug_results
```

### Viewing the HTML Report
The report is written to `<report_dir>/pytest_html_report.html` (default `results/`).

> **Open it over HTTP, not by double-clicking (`file://`).** pytest-html sorts on
> load via `history.pushState`, which throws a `SecurityError` over `file://` when the
> project path contains **non-ASCII characters** — leaving the results table empty.
> Serve it instead:
>
> ```bash
> uv run python -m http.server -d results 8000
> # then open http://localhost:8000/pytest_html_report.html
> ```
>
> (Or keep the checkout under an ASCII-only path, which avoids the issue entirely.)

---

## 3. Test Case Specifications (Framework)

The test cases are located in [test_search.py](file:///Users/huchiawei/Downloads/面試/momo/Sr_Web_Testing_Assignment/suites/SEARCH/test_search.py). Below are their specifications:

| Scenario | Test ID | Method Name | Testing Level (Tier) | Inputs & Outputs | Expected Results |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Scenario 1**: Happy Path Search | `SEARCH-001` | `test_happy_path_search` | RAT (Smoke Test) | **Input**: Valid keyword (e.g. `"iPhone"`)<br>**Output**: Search results page | <ul><li>H1 header text contains the searched keyword.</li><li>Product list contains at least one product.</li></ul><br>*Asserts only the stable search contract; relevance/ordering is momo's ranking output (shifts daily with promos/sponsored slots) and is covered deterministically by SEARCH-005.* |
| **Scenario 2**: Advanced Price Range Filtering | `SEARCH-002` | `test_advanced_price_range_filtering` | TOFT (Functionality & Toleration) | **Input**: Keyword (`"咖啡機"`), Price bounds (`[2000, 5000]`)<br>**Output**: Filtered product grid | <ul><li>Filter successfully submitted.</li><li>Every extracted product price falls within range `[2000, 5000]`.</li></ul> |
| **Scenario 3**: Autocomplete Suggestions | `SEARCH-003` | `test_search_autocomplete_suggestions` | FAST (Core Happy Path) | **Input**: Partial keyword (e.g. `"iPhone"`)<br>**Output**: Autocomplete suggestion dropdown | <ul><li>Suggestions dropdown visible on focus/input.</li><li>Dropdown list is populated (count > 0).</li><li>Clicking suggestion redirects and loads results matching the selected keyword.</li></ul> |
| **Scenario 4**: Negative Path - No Search Results | `SEARCH-004` | `test_negative_no_results` | FET (Functional Edge Test) | **Input**: Gibberish keyword (e.g. `"xyz999abc_not_exist"`)<br>**Output**: Empty state view | <ul><li>Page displays a "No results found" placeholder or "查無商品" indicator.</li><li>Product list count is `0`.</li></ul> |
| **Scenario 5**: Sort by Price (asc & desc) | `SEARCH-005` | `test_sort_by_price_ascending_and_descending` | TOFT (Functionality & Toleration) | **Input**: Keyword (`"行動電源"`), price sort toggled low→high then high→low<br>**Output**: Re-ordered product grid | <ul><li>Organic (non-sponsored) prices are non-decreasing when sorted ascending.</li><li>Organic prices are non-increasing when sorted descending.</li></ul><br>*Sponsored ad slots sit at fixed positions and ignore sorting, so they are excluded; both directions are checked to prove the control actually re-sorts.* |

---

## 4. Playwright Trace Viewer (`trace.zip`)

Playwright Trace Viewer is a graphical user interface tool that allows you to post-mortem explore recorded test traces. It displays a visual timeline, step-by-step DOM snapshots, network requests, console logs, and links execution states directly to source code.

Traces are automatically generated under `results/<SUITE>/<ID>/trace.zip` when the logging level is set to `DEBUG` (e.g. `log_level = DEBUG` in `config.ini` or `-l DEBUG` in the CLI).

### How to Open Traces

You can view the generated `trace.zip` files using the following methods:

#### Method 1: The Online Trace Viewer (Recommended)
This is the easiest method and requires no local installation. The trace file is processed locally inside your browser sandbox and is not uploaded to any server.
1. Open your browser and navigate to **[trace.playwright.dev](https://trace.playwright.dev/)**.
2. Drag and drop the `trace.zip` file (e.g., `results/SEARCH/SEARCH-001/trace.zip`) into the page.

#### Method 2: Via Playwright CLI (Local)
If you have the virtual environment activated, you can open traces directly from your terminal:
```bash
uv run playwright show-trace results/SEARCH/SEARCH-001/trace.zip
```

### Core Features of the Trace Viewer
- **Filmstrip / Timeline**: Hover over the timeline at the top to see screenshot thumbnails showing how the page loaded and transitioned visually.
- **Actions Bar**: The left sidebar lists every Playwright call (clicks, inputs, navigations). Clicking an action displays its details.
- **DOM Snapshots (Before/Action/After)**: The center pane shows the exact rendered state of the DOM at the time of action, allowing you to inspect elements and troubleshoot selectors.
- **Console & Network Tabs**: The bottom pane displays browser console errors/warnings and detailed network request/response headers and payloads.

---

## 5. Resilience & Observability

### Third-Party Network Filtering
momo loads heavy ad/analytics/tracking traffic (Google, Criteo, TikTok, Taboola, Sentry, …) that is irrelevant to the search feature under test. The framework blocks these at the network layer so each test focuses on momo's own flow.
- **Blocklist** (shared, reusable across suites): `suites/common/blocked_hosts.txt` — one registrable domain per line; subdomains match automatically (e.g. `criteo.com` also blocks `gum.criteo.com`).
- **Mechanism**: `BasePage.block_requests()` aborts matching requests; the SEARCH suite wires it in via an autouse fixture in `suites/SEARCH/conftest.py`.
- Each test logs what was applied: `Applied 3rd-party networking filter: blocking N hosts (refer to suites/common/blocked_hosts.txt)`.
- **Extend** it by adding a domain to the file — no code change.

### Performance Instrumentation (`[PERF]` logs)
Key operations (navigate, search, price filter, autocomplete) emit a greppable, machine-parseable `[PERF]` line:
```
[PERF] op=search duration_ms=7873 retries=0 keyword=iPhone
```
`op` = operation, `duration_ms` = latency, `retries` = retries needed (see below). Build a performance matrix by grepping the per-case logs:
```bash
grep -h "\[PERF\]" results/SEARCH/*/test.log
```

### Retry with Backoff (throttling resilience)
momo rate-limits repeated automated traffic, which can intermittently time out navigation/search/filter actions. These operations are wrapped with a shared retry-with-backoff helper (`utils/retry.py`):
- Retries on Playwright `TimeoutError` (and, for the price filter, a dropped-input `AssertionError`) using exponential backoff.
- **Exception-aware backoff:** throttle-class errors (Playwright `TimeoutError`) back off from a longer base (`throttle_delay`, default 5s → 5s, 10s, …) because momo's rate-limit window lasts seconds; structural retryable errors (e.g. a dropped-input `AssertionError`) use the shorter base (`base_delay`, default 1s) since they clear on an immediate re-try. Throttle retries are tagged `kind=throttle` in the `[RETRY]` log.
- Each retry logs a `[RETRY]` warning; the operation's `[PERF]` line then carries `retries=N`.
- **Observe degradation:** `retries=0` is healthy; `retries>0` means the op only succeeded after retrying (slower). Grep for it:
```bash
grep -hE "\[RETRY\]|retries=[1-9]" results/SEARCH/*/test.log
```

### Whole-test Reruns (`--reruns`, opt-in)
`with_retry` absorbs blips *within* an operation, but a hard rate-limit window can outlast its bounded retries and fail the whole test (the kind of failure a single isolated re-run later would pass). `--reruns N` adds a coarser, outer safety net: rerun a **failing test** up to `N` times (after `--reruns-delay` seconds so the throttle window can pass). It is **off by default** (`--reruns 0`).

```bash
# Rerun any failing case up to twice, waiting 5s between attempts
uv run python run_tests.py --reruns 2
```

This is a deliberate trade-off, with two guardrails so it stays honest:
- **Reruns are not scoped to one exception type.** Some transient issues here surface as `AssertionError` (e.g. a dropped filter input, the price-sort settle), so restricting to `TimeoutError` would miss them. The cost: a genuinely flaky/broken case can go green on a rerun.
- **Rerun-rescued cases are flagged, so flakiness is never hidden.** pytest-html renders each failed attempt as a first-class `Rerun` row (with its failure detail) plus the final `Passed` row, and the summary carries a `N rerun` count. On top of that, the reporting hook labels the passing row itself — **"Passed after N rerun(s)"** — and logs a `[WARNING]`. A pass that needed a rerun is therefore always visible for review, not a silent green.

Two layers, plus the suite is built to keep most failures real: operation blips → `with_retry`; a whole test knocked out by noise → `--reruns`.

---

## 6. Git Branching & Development Workflow

To ensure high codebase maintainability and clean history:

1. **Release Branch (`master`)**: Represents stable, production-ready releases. It is **only** updated by merging from `dev` at CI/CD release time — never committed to directly.
2. **Development Branch (`dev`)**: The integration branch and the **GitHub default branch**. All feature branches target and merge into `dev` first (via Pull Request).
3. **Feature Branching (`feature/*`)**: Individual feature tasks are developed on standalone branches branched off `dev`.
   * *Example*: `feature/setup-framework` or `feature/implement-pom`
4. **Commit Conventions**: All commit messages must be prefixed with semantic keywords:
   - `feat: ...` for new features or frameworks (e.g., `feat: implement page objects and selectors`)
   - `fix: ...` for bug fixes or locator correction (e.g., `fix: update autocomplete dropdown locator`)
5. **Flow**:
   - Open a PR: `feature/*` $\rightarrow$ `dev`
   - Test and verify on `dev`
   - At release, merge `dev` $\rightarrow$ `master`.
