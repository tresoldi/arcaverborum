#!/usr/bin/env python3
"""Arca Verborum data explorer (thin entry point).

A small console "database interface" over the aggregate output. Run with
no arguments for detailed help with examples. Run `python explore.py index`
once, then query:

  python explore.py langs --family Indo-European
  python explore.py lang ine-latin
  python explore.py concept WATER --family Indo-European
  python explore.py cognate --concept WATER
  python explore.py form '*water*'
  python explore.py stats --family Indo-European
  python explore.py sql "SELECT tier, COUNT(*) FROM forms GROUP BY tier"
  python explore.py info

All logic lives in arcaverborum.explore (importable and tested).
"""

from __future__ import annotations

import sys

from arcaverborum.explore import main

if __name__ == "__main__":
    sys.exit(main())
