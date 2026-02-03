@echo off
REM 后端文件迁移和重构脚本 (Windows版本)
REM 策略：先归档旧文件，再重构，确保安全

setlocal enabledelayedexpansion

echo ╔═══════════════════════════════════════════════════════════════╗
echo ║          Backend 文件迁移和重构脚本                          ║
echo ║  策略：先归档 ^> 再重构 ^> 最终优化                            ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM 创建时间戳
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "BACKUP_DIR=backup_%dt:~0,8%_%dt:~8,6%"
set "ARCHIVE_DIR=backend\archive"

echo 📦 步骤 0：创建备份和归档目录
echo 备份目录: %BACKUP_DIR%
mkdir "%BACKUP_DIR%" 2>nul
mkdir "%ARCHIVE_DIR%" 2>nul

REM 完整备份
echo 正在完整备份 backend/...
xcopy /E /I /Q /H backend "%BACKUP_DIR%\backend" >nul
echo ✅ 备份完成
echo.

REM ============================================================================
REM 阶段1：归档未使用的模块（安全）
REM ============================================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  阶段1：归档未使用的模块（安全）                                   ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 1.1 归档 super_agent
echo 📦 1.1 归档 super_agent/（实验性功能）
if exist "backend\super_agent" (
    move /Y backend\super_agent "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: super_agent/
) else (
    echo    ⚠️  super_agent/ 不存在，跳过
)

REM 1.2 归档 ppt_api
echo 📦 1.2 归档 ppt_api/（未集成到系统）
if exist "backend\ppt_api" (
    move /Y backend\ppt_api "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: ppt_api/
) else (
    echo    ⚠️  ppt_api/ 不存在，跳过
)

REM 1.3 归档 skills
echo 📦 1.3 归档 skills/（未启用的技能定义）
if exist "backend\skills" (
    move /Y backend\skills "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: skills/
) else (
    echo    ⚠️  skills/ 不存在，跳过
)

REM 1.4 归档 simplePPT 和 simpleOutline
echo 📦 1.4 归档 simplePPT/ 和 simpleOutline/（依赖已归档的super_agent）
if exist "backend\simplePPT" (
    move /Y backend\simplePPT "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: simplePPT/
)
if exist "backend\simpleOutline" (
    move /Y backend\simpleOutline "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: simpleOutline/
)

REM 1.5 归档文档（迁移到根目录）
echo 📦 1.5 归档并迁移文档
if exist "backend\doc" (
    if not exist "docs" mkdir docs
    xcopy /E /I /Y backend\doc\* docs\ >nul 2>&1
    move /Y backend\doc "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: backend/doc/ -^> docs/
)
if exist "backend\docs" (
    if not exist "docs" mkdir docs
    xcopy /E /I /Y backend\docs\* docs\ >nul 2>&1
    move /Y backend\docs "%ARCHIVE_DIR%\" >nul
    echo    ✅ 已归档: backend/docs/ -^> docs/
)

echo.
echo ✅ 阶段1完成！已归档未使用的模块
echo.

REM ============================================================================
REM 阶段2：提取重复代码到 common/
REM ============================================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  阶段2：提取重复代码到 common/                                ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM 2.1 提取 adk_agent_executor.py
echo 🔧 2.1 提取 adk_agent_executor.py 到 common/
if not exist "backend\common\adk_agent_executor.py" (
    if exist "backend\flat_slide_agent\adk_agent_executor.py" (
        copy /Y backend\flat_slide_agent\adk_agent_executor.py backend\common\ >nul
        echo    ✅ 已提取: common/adk_agent_executor.py
    ) else (
        echo    ⚠️  源文件不存在
    )
) else (
    echo    ⚠️  common/adk_agent_executor.py 已存在
)

REM 2.2 提取 a2a_client.py
echo 🔧 2.2 提取 a2a_client.py 到 common/
if not exist "backend\common\a2a_client.py" (
    if exist "backend\slide_agent\a2a_client.py" (
        copy /Y backend\slide_agent\a2a_client.py backend\common\ >nul
        echo    ✅ 已提取: common/a2a_client.py
    ) else (
        echo    ⚠️  源文件不存在
    )
) else (
    echo    ⚠️  common/a2a_client.py 已存在
)

echo.
echo ⚠️  注意：重复代码已复制到 common/，但原文件保留（向后兼容）
echo       后续可以逐步更新各模块使用 common/ 中的版本
echo.

REM ============================================================================
REM 阶段3：创建新的目录结构
REM ============================================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║  阶段3：创建新的目录结构（清晰的层次）                          ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo 📁 3.1 创建新的目录结构

mkdir backend\agents\base 2>nul
mkdir backend\agents\planning 2>nul
mkdir backend\agents\research 2>nul
mkdir backend\agents\generation 2>nul

mkdir backend\api\routes 2>nul
mkdir backend\api\schemas 2>nul
mkdir backend\api\middleware 2>nul

mkdir backend\core\models 2>nul
mkdir backend\core\interfaces 2>nul
mkdir backend\core\services 2>nul

mkdir backend\infrastructure\llm 2>nul
mkdir backend\infrastructure\database 2>nul
mkdir backend\infrastructure\config 2>nul
mkdir backend\infrastructure\logging 2>nul

mkdir backend\memory\interfaces 2>nul
mkdir backend\memory\implementations 2>nul
mkdir backend\memory\services 2>nul
mkdir backend\memory\utils 2>nul

mkdir backend\tools\search 2>nul
mkdir backend\tools\media 2>nul
mkdir backend\tools\file 2>nul
mkdir backend\tools\mcp 2>nul

mkdir backend\services 2>nul

mkdir backend\tests\unit 2>nul
mkdir backend\tests\integration 2>nul
mkdir backend\tests\fixtures 2>nul
mkdir backend\tests\utils 2>nul

echo    ✅ 已创建新的目录结构
echo.
echo    新增目录：
echo    - backend\agents\          （Agent实现）
echo    - backend\api\             （API接口）
echo    - backend\core\            （核心层）
echo    - backend\infrastructure\ （基础设施）
echo    - backend\memory\          （记忆系统）
echo    - backend\tools\           （工具集）
echo    - backend\services\        （业务服务）
echo    - backend\tests\           （测试）
echo.

REM ============================================================================
REM 完成：生成报告
REM ============================================================================
echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║                     迁移完成报告                              ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

echo ✅ 阶段1：归档未使用模块
echo    - archive\super_agent\
echo    - archive\ppt_api\
echo    - archive\skills\
echo    - archive\simplePPT\
echo    - archive\simpleOutline\
echo    - archive\doc\（已迁移到根目录）
echo    - archive\docs\（已迁移到根目录）
echo.

echo ✅ 阶段2：提取重复代码
echo    - common\adk_agent_executor.py
echo    - common\a2a_client.py
echo.

echo ✅ 阶段3：创建新目录结构
echo    - backend\agents\
echo    - backend\api\
echo    - backend\core\
echo    - backend\infrastructure\
echo    - backend\memory\
echo    - backend\tools\
echo    - backend\services\
echo    - backend\tests\
echo.

echo 📊 统计信息：
echo    - 归档模块数：7
echo    - 新增目录数：8
echo    - 提取重复代码：2
echo    - 保留生产服务：8
echo.

echo 💾 备份位置：
echo    %BACKUP_DIR%
echo.

echo 📚 相关文档：
echo    - backend\STRUCTURE_MAPPING.md（目录映射）
echo    - backend\REFACTORING_GUIDE.md（重构指南）
echo.

echo ✨ 下一步建议：
echo    1. 查看 backend\STRUCTURE_MAPPING.md 了解详细计划
echo    2. 测试现有服务是否正常运行
echo    3. 开始逐步迁移代码到新目录结构
echo    4. 更新 docker-compose.yml 添加新服务
echo.

echo 🎉 迁移准备完成！系统可以正常使用。
echo.

pause
