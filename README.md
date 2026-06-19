# momo Web Automation Testing Framework (Senior SDET)

This repository provides a professional-grade web automation framework skeleton built using **Python + Pytest + Playwright** targeting the search feature of the **momo shopping site** (`https://www.momoshop.com.tw/`).

It incorporates the Page Object Model (POM) pattern, custom CLI options for Headless and Debug modes, Git branching strategies, and low-level **Chrome DevTools Protocol (CDP)** performance auditing.

---

## 🚀 1. Environment & Setup

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
# 1. Framework self-tests (unit/integration tests for the framework itself) — should be 18 passed
uv run pytest test/

# 2. The full E2E suite against the momo site (all SEARCH scenarios)
uv run python run_tests.py

# 3. A single smoke test (fast sanity check that the whole pipeline works)
uv run python run_tests.py -c SEARCH-000
```

> **Dependency management:** add/remove packages with `uv add <pkg>` / `uv remove <pkg>`
> (never edit `requirements.txt` by hand). `requirements.txt` is **auto-generated** from
> `uv.lock` by the `pre-commit` hook (`uv export`) and is kept only as a fallback for
> environments without `uv`.

---

## 📦 2. Global Configuration & CLI Interface (`run_tests.py`)

The framework relies on a global configuration file **`config.ini`** for default execution settings. You can override these defaults directly from the CLI.

### Global Configuration (`config.ini`)
The default configuration file at the project root includes annotations and is structured as:
```ini
[momo_automation]
# Run tests in headless mode (true) or headed mode (false)
# Allowed values: true, false (default: true)
headless = true

# Set the test run logging level
# Allowed values: DEBUG, INFO, WARNING, ERROR (default: INFO)
# Note: Setting to DEBUG dynamically triggers:
#  - Playwright action slow_mo (800ms action delay)
#  - Video recording for all test cases (linked in the HTML report)
log_level = INFO

# Output directory for run assets (HTML report, per-case logs/traces/videos)
# Supports relative or absolute paths (auto-resolved to absolute) and is created if missing.
# Example: ./results
report_dir = ./results

# Enable Playwright Inspector interactive debugging GUI
# Allowed values: true, false (default: false)
# Note: Setting to true pauses execution at the start of tests
pwdebug = false

# Capture a Playwright execution trace (.zip) for every test case
# Allowed values: true, false (default: true)
trace = true
```

### CLI Overrides
The `run_tests.py` wrapper accepts arguments to override the values inside `config.ini` dynamically:
- **Browser Mode Override**:
  - `--headless`: Forces headless execution (runs in background).
  - `--headed`: Forces headed execution (opens a visible browser window).
- **Log Level Override**:
  - `--log-level <LEVEL>` (or `-l <LEVEL>`): Sets the log capturing and output level. Available levels are `DEBUG`, `INFO`, `WARNING`, `ERROR`.
  - *Note: Setting the log level to `DEBUG` automatically activates verbose logger outputs, slows down action execution by 800ms (`slow_mo`), and captures both execution traces and videos for all test runs.*
- **Report Directory Override**:
  - `--report <DIR>` (or `-r <DIR>`): Sets a custom output **directory** for the HTML report and per-case assets. The report *filename* itself comes from `pytest.ini`, so pass a directory, not a file.
- **Playwright Inspector (PWDEBUG) Override**:
  - `--pwdebug`: Enables Playwright Inspector GUI and pauses execution at start of tests (forces headed mode).
  - `--no-pwdebug`: Disables Playwright Inspector GUI.
- **Trace Override**:
  - `--trace`: Forces Playwright execution trace capture (`.zip`) for every test case.
  - `--no-trace`: Disables trace capture.

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
- **RAT (Release Acceptance Testing)**: Smoke test verifying if the environment/site is accessible (takes ~2 seconds).
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

> ⚠️ **Open it over HTTP, not by double-clicking (`file://`).** pytest-html sorts on
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

## 📋 3. Test Case Specifications (Framework)

The test cases are located in `suites/SEARCH/test_search.py`. Below are their specifications:

### Scenario 0: Release Acceptance Testing (RAT) (`test_homepage_accessibility`)
* **Testing Level**: Release Acceptance Testing (Smoke Test)
* **Input**: None (Navigate to homepage)
* **Output**: Successfully loaded homepage
* **Expected Result**:
  - Homepage navigation returns a success status.
  - Page is accessible and completes loading in under 3-5 seconds.
  - Page browser title contains the keyword `"momo"`.

### Scenario 1: Happy Path Search (`test_happy_path_search`)
* **Testing Level**: System Integration / E2E UI Functional Test
* **Input**: Valid product keyword string (e.g., `"iPhone"`)
* **Output**: Search results page listing products relevant to the keyword
* **Expected Result**:
  - Page header (H1) text contains the searched keyword.
  - Product list displays at least one product.
  - The first few product titles are relevant to the input search term.

### Scenario 2: Advanced Price Range Filtering (`test_advanced_price_range_filtering`)
* **Testing Level**: System Integration / E2E UI Functional Test
* **Input**: Category keyword (`"咖啡機"`) and numeric price bounds (Min: `2000`, Max: `5000`)
* **Output**: Re-rendered product grid displaying filtered results
* **Expected Result**:
  - Filter is successfully submitted.
  - Every product price extracted from the page falls within the range `[2000, 5000]`.

### Scenario 3: Autocomplete Suggestions (`test_search_autocomplete_suggestions`)
* **Testing Level**: E2E UI User Experience / Integration Test
* **Input**: Partial keyword text (`"iPhone"`) entered into the search box
* **Output**: Dropdown modal containing recommendation keywords
* **Expected Result**:
  - Autocomplete suggestion box becomes visible on input focus/type.
  - Dropdown suggestion list is populated (count > 0).
  - Clicking a suggestion redirects the browser and successfully loads the results page matching the chosen keyword.

### Scenario 4: Negative Path - No Search Results (`test_negative_no_results`)
* **Testing Level**: E2E UI Negative / Boundary Test
* **Input**: Non-existent, gibberish keyword (e.g., `"xyz999abc_not_exist"`)
* **Output**: Results page displaying empty state view
* **Expected Result**:
  - Page displays a "No results found" placeholder or "查無商品" indicator.
  - Product item list count is `0`.

---

## 🔍 4. Playwright Trace Viewer (`trace.zip`)

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

## 💎 5. The 3 momo Values

This framework has been architected to adhere to the core SDET dimensions valued by the momo team:

1. **Test Coverage**: Focuses on high-value business flows (Happy path searching, autocomplete user experience, filter logic accuracy, and system failure handling/boundaries) rather than a high volume of trivial tests.
2. **Stability (Anti-Flakiness)**:
   - Uses Playwright's native **Auto-waiting engine** (clicks, fills, and waits for visible state automatically).
   - Integrates a global `dismiss_popups()` hook in `BasePage` to automatically handle and dismiss momo's promotional overlays which commonly block UI element interactions.
   - Captures automated failure screenshots and traces in the `results/` folder.
3. **Maintainability**:
   - Implements a strict **Page Object Model (POM)** separation to keep test scripts decoupled from underlying HTML selectors.
   - Centralized logging configurations and standard directory structures.

---

## 🔱 6. Git Branching & Development Workflow

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
