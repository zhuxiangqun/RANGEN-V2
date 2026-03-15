# Archived Files

This directory contains deprecated langgraph workflow files.

> ⚠️ These files have been deprecated as of 2026-03-12.
> See `src/core/WORKFLOW_STATUS.md` for details.

## Status: Archived (Not Deleted)

These files are moved here but NOT deleted - they can be restored if needed.

### Files in this archive:

1. **langgraph_layered_workflow.py** - 未使用 (备用工作流)
2. **langgraph_layered_workflow_fixed.py** - 未使用
3. **simplified_layered_workflow.py** - 未使用
4. **simplified_business_workflow.py** - 未使用
5. **enhanced_simplified_workflow.py** - 未使用
6. **langgraph_dynamic_workflow.py** - 未使用

## Restoration

If you need to restore any file:
```bash
git checkout HEAD -- src/core/archive/<file>
```

## Alternative

Instead of restoring, consider:
1. Using ExtendedAgentState from `unified_state.py`
2. Using EnhancedExecutionCoordinator from `enhanced_execution_coordinator.py`
