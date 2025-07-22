# Aio Adaptive

Project is based off of [Netflix Concurrency](https://github.com/Netflix/concurrency-limits), but for python!
The initial setup allows for someone to configure the Vegas adaptive rate limit.

See the examples below for how to leverage it.

## Install

TODO

## Developer Setup

1. Navigate to the Server Directory

   ```bash
   cd aioadaptive
   ```

2. Install Server Requirements

   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv sync
   ```

3. Run tests

   ```bash
   pytest
   ```
