@echo off
setlocal

REM Usage: run_gemini_tests.bat [keys] [model]
REM Example: run_gemini_tests.bat "KEY1,KEY2,KEY3" gemini-1.5-flash

set KEYS=%~1
set MODEL=%~2
if "%MODEL%"=="" set MODEL=gemini-1.5-flash

if "%KEYS%"=="" (
  echo Using keys from GEMINI_API_KEYS in .env (if available)
  python test_gemini_apis.py --model "%MODEL%"
) else (
  python test_gemini_apis.py --keys "%KEYS%" --model "%MODEL%"
)

endlocal
