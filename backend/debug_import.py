"""Debug import issues"""
import sys
import os
import time

start_time = time.time()

def log_step(step_name):
    elapsed = time.time() - start_time
    print(f"[{elapsed:.2f}s] {step_name}")

try:
    log_step("Step 1: Import os")
    import os
    log_step("  Success")

    log_step("Step 2: Import secrets")
    import secrets
    log_step("  Success")

    log_step("Step 3: Import logging")
    import logging
    log_step("  Success")

    log_step("Step 4: Import enum")
    from enum import Enum
    log_step("  Success")

    log_step("Step 5: Import typing")
    from typing import Dict, List, Optional, Any
    log_step("  Success")

    log_step("Step 6: Import pydantic_settings.BaseSettings")
    from pydantic_settings import BaseSettings
    log_step("  Success")

    log_step("Step 7: Import pydantic")
    from pydantic import Field
    log_step("  Success")

    log_step("Step 8: Set environment variables")
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['JWT_SECRET_KEY'] = 'test_secret_key_12345678901234567890'
    log_step("  Success")

    log_step("Step 9: Import infrastructure.config.common_config (classes only)")
    from infrastructure.config.common_config import Environment, ModelProvider
    log_step("  Success")

    log_step("Step 10: Import AppConfig class")
    from infrastructure.config.common_config import AppConfig
    log_step("  Success")

    log_step("Step 11: Create AppConfig instance")
    config = AppConfig()
    log_step("  Success")

    log_step("All imports successful!")

except Exception as e:
    log_step(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
