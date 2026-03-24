#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN 评测系统入口点

支持运行方式:
- python -m evaluation          # 运行V1评估 (7维度)
- python -m evaluation v2       # 运行V2评估 (24维度)
"""

import sys
import asyncio

from .v2_capability.runner import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ 评估被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"❌ 评估失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
