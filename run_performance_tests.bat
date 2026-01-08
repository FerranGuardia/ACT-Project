@echo off
REM ACT Project - Performance Test Runner
REM Runs performance benchmarks and analysis

cd /d "%~dp0"

echo ========================================
echo    ACT Project - Performance Testing
echo ========================================
echo.
echo Current directory: %CD%
echo.

echo ========================================
echo    Running Performance Analysis
echo ========================================
echo.
echo Analyzing test performance and identifying slow tests...
echo.

python tests/scripts/analyze_test_performance.py --slow-threshold 2.0 --output performance_report.md

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [PASS] Performance analysis completed
    echo Check performance_report.md for detailed results
) else (
    echo.
    echo [FAIL] Performance analysis failed
)

echo.
echo ========================================
echo    Running Performance Benchmarks
echo ========================================
echo.
echo Running performance benchmarks...
echo This may take several minutes...
echo.

pytest tests/unit/tts/test_performance_benchmarks.py -v --benchmark-only --benchmark-json=benchmark_results.json

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [PASS] Performance benchmarks completed
    echo Check benchmark_results.json for detailed results
) else (
    echo.
    echo [FAIL] Performance benchmarks failed
)

echo.
echo ========================================
echo    Running Property-Based Tests
echo ========================================
echo.
echo Running property-based tests with Hypothesis...
echo.

pytest tests/unit/tts/test_property_based.py -v --tb=short

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [PASS] Property-based tests completed
) else (
    echo [FAIL] Property-based tests failed
)

echo.
echo ========================================
echo    Performance Testing Complete
echo ========================================
echo.
echo Results saved to:
echo - performance_report.md
echo - benchmark_results.json
echo.

pause
