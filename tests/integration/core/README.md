# Core Module Integration Tests

Integration tests for core components that serve as the foundation for the entire application.

## Overview

These tests verify that core components work correctly together and handle real-world scenarios that unit tests cannot cover. Core components include:

- **ConfigManager** - Configuration persistence and management
- **MetadataManager** - Novel metadata storage
- **ACTLogger** - Centralized logging
- **ErrorHandling** - Cross-module error propagation

## Test Coverage

### ConfigManager Integration Tests

The ConfigManager is the most critical core component as it affects every other module in the system. These tests cover:

#### 1. Application Startup Sequence
- **Purpose**: Verify ConfigManager initializes correctly during application startup
- **What it tests**:
  - ConfigManager singleton creation
  - Directory creation (`.act` folder)
  - Default configuration loading
  - Logger initialization with config
  - MetadataManager initialization with config

#### 2. Persistence Across "Application Sessions"
- **Purpose**: Ensure config changes persist between application "restarts"
- **What it tests**:
  - Config file creation and writing
  - Config file reading on subsequent loads
  - Complex nested configuration structures
  - Singleton behavior across simulated restarts

#### 3. File Corruption Recovery
- **Purpose**: Verify graceful handling of corrupted config files
- **What it tests**:
  - Invalid JSON recovery
  - Fallback to defaults
  - Automatic config file regeneration
  - Error logging during recovery

#### 4. Cross-Module Configuration Dependencies
- **Purpose**: Test that other modules correctly use ConfigManager values
- **What it tests**:
  - PipelineOrchestrator using config voice settings
  - ProjectManager using config path settings
  - FileManager using config directory paths
  - Real component interactions with config

#### 5. Configuration Changes Propagation
- **Purpose**: Ensure config changes are immediately visible to dependent components
- **What it tests**:
  - Dynamic config updates
  - Multiple component instances seeing same config
  - Config value consistency across components

#### 6. Environment-Specific Behavior
- **Purpose**: Verify config behaves differently in test vs production
- **What it tests**:
  - Test environment detection
  - Temp directory usage in tests
  - Path validation in test environments

#### 7. Path Validation Integration
- **Purpose**: Test path validation works in real scenarios
- **What it tests**:
  - Valid absolute paths accepted
  - Problematic paths (Desktop, root) rejected
  - Relative paths converted to defaults
  - Path resolution edge cases

#### 8. Error Isolation
- **Purpose**: Ensure config errors don't crash dependent components
- **What it tests**:
  - File permission errors handled gracefully
  - Components continue working with defaults
  - Error logging during failures
  - Recovery mechanisms

#### 9. Version File Integration
- **Purpose**: Verify version information integration
- **What it tests**:
  - Version reading from VERSION file
  - Version included in config structure
  - Version consistency across components

## Critical Vulnerabilities Caught

These integration tests catch vulnerabilities that unit tests miss:

1. **Singleton Initialization Race Conditions**: Multiple components initializing ConfigManager simultaneously
2. **File System Permission Issues**: Config directory creation failures
3. **Path Resolution Failures**: Invalid paths causing downstream component failures
4. **JSON Corruption Silent Failures**: Corrupted config files leading to inconsistent state
5. **Cross-Module Dependency Breaks**: One module's config changes affecting others unexpectedly
6. **Environment Detection Bugs**: Test vs production path confusion
7. **Version Synchronization Issues**: VERSION file changes not reflected in config

## Running the Tests

```bash
# Run all core integration tests
pytest tests/integration/core/ -v

# Run specific ConfigManager test
pytest tests/integration/core/test_config_manager_integration.py::TestConfigManagerIntegration::test_config_persistence_across_restarts -v

# Run with coverage
pytest tests/integration/core/ --cov=src.core --cov-report=html
```

## Test Architecture

- **Serial Execution**: Tests marked with `@pytest.mark.serial` to prevent singleton interference
- **Temp Directories**: Each test uses isolated temp directories to avoid conflicts
- **Singleton Reset**: Automatic singleton cleanup between tests
- **Real Components**: Tests use actual components, not mocks (except where necessary)

## Dependencies

These tests integrate with:
- `src.core.config_manager.ConfigManager`
- `src.core.metadata_manager.MetadataManager`
- `src.core.logger.ACTLogger`
- `src.processor.pipeline_orchestrator.PipelineOrchestrator`
- `src.processor.project_manager.ProjectManager`
- `src.processor.file_manager.FileManager`

## Next Steps

After implementing these ConfigManager integration tests, consider similar integration test suites for:

1. **Logger Integration Tests** - Logging system with all components
2. **MetadataManager Integration Tests** - Metadata persistence and cross-component usage
3. **Error Handling Integration Tests** - Error propagation across module boundaries
4. **Full Application Startup Integration** - Complete `main.py` initialization sequence