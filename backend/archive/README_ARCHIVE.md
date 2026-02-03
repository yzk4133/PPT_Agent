# Backend Archive Directory

This directory contains archived modules and temporary code from the backend refactoring process.

## 📦 Archived Modules

### 1. Old Architecture Modules (Legacy)

| Module | Description | Replacement | Status |
|--------|-------------|-------------|--------|
| `slide_agent/` | Old layered architecture for PPT generation | ✅ `agents/applications/ppt_generator/` | **Deprecated** |
| `slide_outline/` | Old outline generation module | ✅ `agents/applications/outline_generator/` | **Deprecated** |
| `simplePPT/` | Simplified PPT generation prototype | ✅ `agents/applications/ppt_generator/` | **Deprecated** |
| `simpleOutline/` | Simplified outline generation prototype | ✅ `agents/applications/outline_generator/` | **Deprecated** |

### 2. Development/Experimental Modules

| Module | Description | Status |
|--------|-------------|--------|
| `super_agent/` | Text-based multi-agent system prototype | **Experimental** |
| `ppt_api/` | Old PPT generation API | **Deprecated** |

### 3. Coordination Modules

| Module | Description | Status |
|--------|-------------|--------|
| `hostAgentAPI/` | A2A (Agent-to-Agent) host agent API | **Infrastructure** |
| `multiagent_front/` | Frontend interface for multi-agent system | **UI Layer** |

## 🔙 How to Restore

### Restore a Single Module

```bash
# Example: Restore slide_agent
mv backend/archive/slide_agent backend/
```

### Restore All Archived Modules

```bash
cd backend/archive
mv slide_agent ../
mv slide_outline ../
mv simplePPT ../
mv simpleOutline ../
mv ppt_api ../
mv super_agent ../
mv hostAgentAPI ../
mv multiagent_front ../
```

### Complete Rollback

To restore the entire backend to its pre-archive state, you would need to:

1. Restore all archived modules (see above)
2. Revert directory reorganization:
   - Move `agents/core/*` back to `agents/`
   - Move `agents/applications/ppt_generator` to `flat_slide_agent`
   - Move `agents/applications/outline_generator` to `flat_slide_outline`
   - Move `memory/core` to `persistent_memory`
   - Move `memory/basic` to `memory`
   - Move `skills` to `skill_framework`
   - Move `utils/save_ppt` to `save_ppt`
   - Move `utils/common` to `common`

## 📝 Archiving Date

**Date**: 2026-02-02
**Reason**: Backend directory structure cleanup and simplification
**Impact**: Reduced top-level directories from 23 to 12 (48% reduction)

## ⚠️ Important Notes

1. **Code Preservation**: All code in this archive is preserved exactly as it was
2. **Git History**: File moves are tracked by Git, so history is preserved
3. **Not Deleted**: Nothing is permanently deleted - everything can be restored
4. **Reference Only**: These modules are kept for reference purposes only
5. **No Active Development**: Do not develop new features in archived modules

## 🚀 New Architecture

After archiving, the backend now follows a cleaner structure:

```
backend/
├── agents/              # Unified agent management
│   ├── core/            # Core agent implementations
│   └── applications/    # Agent applications
├── memory/              # Unified memory management
│   ├── core/            # Persistent memory
│   └── basic/           # Basic memory
├── skills/              # Skill framework
├── utils/               # Common utilities
├── api/                 # API layer
├── core/                # Core layer
├── services/            # Service layer
├── infrastructure/      # Infrastructure layer
└── tools/               # Tools layer
```

For questions about the new architecture, see `../README.md` and `../ARCHITECTURE.md`.
