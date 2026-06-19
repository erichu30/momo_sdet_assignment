# 🛠️ 框架自我測試說明文件 (Framework Self-Testing)

本目錄 (`test/`) 專門存放**測試此自動化框架本身**的單元測試 (Unit Tests) 與整合測試 (Integration Tests)，主要驗證 CLI 執行器、設定檔讀取器、測試案例 ID 解析器與環境變數控制項目的正確性，以確保測試工具本身的穩定與健全，不影響主要 E2E 測試流程。

---

## 📂 測試目錄結構

```text
test/
├── README.md         # 本說明文件
├── test_cli.py       # 測試 CLI 參數解析、覆蓋優先權、連鎖效能與環境變數設定
├── test_config.py         # 測試 config.ini 與 pytest.ini 的載入、解構與預設 fallback 機制
├── test_helpers.py        # 測試 utils/test_case_parser.py 的測試案例 ID (例如 SEARCH-001) 與範圍解析器
└── test_runtime_config.py # 測試 utils/runtime_config.py 的環境變數解析,以及與 run_tests.py 的 producer/consumer 一致性
```

---

## ⚙️ 重構設計與技術亮點

### 1. `run_tests.py` 可測試性重構 (Testability Refactoring)
* **問題**：原本的 `run_tests.py` 的解析與環境設定代碼全部寫在 `main()` 函式內，且尾端直接呼叫 `pytest.main()` 與 `sys.exit()`。這導致在撰寫單元測試時，呼叫該邏輯會直接導致測試行程結束或觸發真實 Pytest 執行。
* **作法**：我們將邏輯抽離並模組化為以下方法：
  * `build_parser()`: 僅建立並返回 `argparse.ArgumentParser` 物件。
  * `resolve_configurations(args, defaults)`: 負責處理設定檔預設值與 CLI 覆蓋的運算邏輯，匯出環境變數，並回傳解析後的 Pytest 參數字典。
* **好處**：測試腳本可以傳入 mock 參數直接測試這兩個函式，確保各種 CLI 參數組合的解析正確，完全不影響測試環境。

### 2. 環境變數隔離與還原機制 (Environment Isolation)
* **問題**：測試 CLI 參數時，系統會修改 `os.environ`（如設定 `MOMO_HEADLESS`、`PWDEBUG` 等）。如果沒有清理，前一個測試的設定會污染後續測試的環境。
* **作法**：在 `test_cli.py` 的基底類別中使用 `setUp()` 與 `tearDown()` 備份與還原 `os.environ`：
  ```python
  def setUp(self):
      self.original_env = dict(os.environ)

  def tearDown(self):
      os.environ.clear()
      os.environ.update(self.original_env)
  ```

### 3. 虛擬檔案系統 Mocking (File System Mocking)
* **問題**：若測試需要讀取不同的 `config.ini` 或 `pytest.ini`，在實體硬碟上反覆建立、刪除檔案會造成 I/O 負擔，也容易殘留髒檔案。
* **作法**：使用 `unittest.mock.patch` 動態 mock `os.path.exists`，並配合 `mock_open` 模擬檔案讀取內容，完全在記憶體中進行虛擬檔案讀取測試：
  ```python
  @patch("os.path.exists")
  @patch("builtins.open", new_callable=mock_open, read_data="[momo_automation]\nheadless = false")
  def test_load_config(self, mock_file, mock_exists):
      mock_exists.return_value = True
      # 載入邏輯將會讀取到上面的字串內容
      configs = load_config()
  ```

---

## 🚀 執行自我測試

由於測試模組需要引用根目錄下的 `run_tests.py` 與 `suites`，執行測試時必須將目前工作目錄加入 Python 搜尋路徑 (`PYTHONPATH`)。

### 執行指令：
```bash
PYTHONPATH=. .venv/bin/pytest test/
```

### 驗證設計點一覽：
* [x] **INI Fallback 機制**：檔案缺失時自動載入安全預設值。
* [x] **CLI 優先權覆蓋**：命令列傳入 `--headed` 可以成功覆蓋 INI 檔中的 `headless = true`。
* [x] **PWDEBUG 連鎖效能**：啟用 `--pwdebug` 時，系統自動調整 `MOMO_HEADLESS = false`，並設定環境變數 `PWDEBUG = 1`。
* [x] **測試 Tier 轉換**：將 `--tier RAT,FAST` 正確翻譯成 Pytest `-m "rat or fast"` 參數。
* [x] **ID 自動補零與範圍解構**：輸入 `SEARCH-{1..3}` 能解構成 `SEARCH-001`, `SEARCH-002`, `SEARCH-003`。
