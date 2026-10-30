# orders app

## Data flow

`update_orders` → `DecwareOrderScraper.run()` (`scraper.py`: Selenium/Chrome downloads the CSV from orders.decware.com, parses it, upserts `OrderRecord`, writes `StatusHistory`, marks missing orders `removed_at`). On success it calls `compute_estimates` (`estimation.py`). On failure it raises `CommandError` so the scheduler sees a non-zero exit.

## Gotchas

- **Order identity is a composite key** (customer name, model, base, volts, origin), not a Decware ID. When Decware edits an order, the old record looks removed and a new record appears.
- **`StatusHistory.is_observed=False`** means the timestamp is not when the change happened: either the order's first row, or a change found after missed scraper runs. Exclude these rows from duration statistics.
- **History gap:** the scraper was down ~2025-05-27 → 2026-10-27. Transitions stamped 2026-10-27 and the 2025-04-17 initial import are not real stage durations.
- **Estimation is a statistical queue model** (FIFO position ÷ start rate, plus build time). No LLM. `estimated_date` is the best guess; `FAST_RATE_FACTOR` and `SLOW_RATE_FACTOR` set the early (`range_start_date`) and late (`range_end_date`) ends of the range. Validate any change with `compute_estimates --backtest YYYY-MM-DD`.
- CSV dates contain invisible characters. Use the scraper's existing cleaning/parsing helpers; `tests_date_parsing.py` covers them.
- Production code has no test-mode branches. The one guard: with `test_settings.TESTING = True`, `DecwareOrderScraper._init_driver` raises instead of launching Chrome. Tests patch `_init_driver` with a fake driver (see `ScraperRunTests`) and write real CSV files for `parse_csv`.
- CSV rows are skipped on a bad date; an unknown status is logged and the order keeps its current status (new orders with an unknown status aren't created). A composite key repeated within one CSV is applied once (first row wins).

## Tests

One file per area: `tests_models.py`, `tests_scraper.py`, `tests_estimation.py`, `tests_serializers.py`, `tests_views.py`, `tests_date_parsing.py`. Run them from the repo root with `--settings=decware_order_tracker.test_settings`.
