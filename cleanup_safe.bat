@echo off
REM 保守清理方案 - Windows版本
REM ✅ 安全：不影响任何现有功能

setlocal enabledelayedexpansion

echo ====================================
echo 🧹 保守清理方案 (Windows)
echo ====================================
echo.

REM 创建备份
set BACKUP_DIR=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_DIR=%BACKUP_DIR: =0%
mkdir "%BACKUP_DIR%"
echo 📦 创建备份: %BACKUP_DIR%
xcopy /E /I /Q backend "%BACKUP_DIR%\backend" >nul

REM 删除未使用的ppt_api
echo.
echo 🗑️  1/4: 删除 ppt_api (完全未使用)...
if exist "backend\ppt_api" (
    rmdir /S /Q backend\ppt_api
    echo ✅ 已删除 ppt_api/
) else (
    echo ⚠️  ppt_api 不存在，跳过
)

REM 删除空壳目录
echo.
echo 🗑️  2/4: 删除 super_agent 的空子模块...
if exist "backend\super_agent\simpleArtical" (
    rmdir /S /Q backend\super_agent\simpleArtical
    echo ✅ 已删除 super_agent/simpleArtical/
)

if exist "backend\super_agent\simpleOutline" (
    rmdir /S /Q backend\super_agent\simpleOutline
    echo ✅ 已删除 super_agent/simpleOutline/
)

REM 迁移文档
echo.
echo 🗑️  3/4: 迁移文档到根目录...
if exist "backend\doc" (
    if not exist "docs" mkdir docs
    xcopy /E /I /Y backend\doc\* docs\ >nul 2>&1
    rmdir /S /Q backend\doc
    echo ✅ 已迁移 backend/doc/
)

if exist "backend\docs" (
    if not exist "docs" mkdir docs
    xcopy /E /I /Y backend\docs\* docs\ >nul 2>&1
    rmdir /S /Q backend\docs
    echo ✅ 已迁移 backend/docs/
)

REM 清理测试文件（可选）
echo.
set /p DELETE_TESTS="🗑️  4/4: 是否删除测试文件? (y/N): "
if /i "%DELETE_TESTS%"=="y" (
    del /Q backend\test_*.py 2>nul
    del /Q backend\demo_*.py 2>nul
    echo ✅ 已删除测试文件
)

echo.
echo ====================================
echo ✅ 保守清理完成！
echo ====================================
echo.
echo 📊 清理结果:
echo    - 删除: ppt_api/ (未使用)
echo    - 删除: super_agent/simpleArtical/ (空壳)
echo    - 删除: super_agent/simpleOutline/ (空壳)
echo    - 迁移: doc/ 和 docs/ → 项目根目录
echo.
echo 💾 备份位置: %BACKUP_DIR%
echo.
echo ⚠️ 注意：以下模块仍然保留（需要手动评估）
echo    - super_agent/ (实验性功能)
echo    - multiagent_front/ (Web前端)
echo    - simplePPT/ 和 simpleOutline/ (被super_agent使用)
echo    - slide_agent/ (被flat_slide_agent依赖，需重构)
echo.
echo 💡 提示：如果确认不需要，可以手动删除这些模块
echo.

pause
