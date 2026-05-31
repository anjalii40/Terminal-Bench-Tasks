A Python script at `/app/processor.py` increments a shared counter using concurrent async workers. The number of workers and increments per worker are configured in `/app/config.json`.

The script has a bug that causes the final counter value to be incorrect due to a concurrency issue.

Fix the bug in `/app/processor.py` so the script always produces the correct result.

Run the fixed script:
Output will be written to `/app/output.txt`.
Output must contain exactly one integer followed by a newline.
The expected value is `workers * increments` from `/app/config.json`.
