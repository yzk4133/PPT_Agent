"""
Logger Config 测试
"""

import pytest
import logging
import tempfile
import json
from pathlib import Path
from infrastructure.logger_config.logger_config import (
    SensitiveDataFilter,
    JSONFormatter,
    TextFormatter,
    setup_logger,
    get_logger,
    set_request_id,
    get_request_id,
    LoggerContext,
)

@pytest.mark.unit
class TestSensitiveDataFilter:
    """测试敏感信息过滤器"""

    def test_filter_api_key(self):
        """测试过滤 API Key"""
        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="API Key: sk-1234567890abcdef",
            args=(),
            exc_info=None,
        )

        result = filter_obj.filter(record)

        assert result is True
        assert "sk-***bcdef" in record.msg

    def test_filter_jwt(self):
        """测试过滤 JWT"""
        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test",
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        # JWT 应该被部分脱敏
        assert "eyJ" in record.msg or "***" in record.msg

    def test_filter_password(self):
        """测试过滤密码"""
        filter_obj = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg='password: "mypassword123"',
            args=(),
            exc_info=None,
        )

        filter_obj.filter(record)

        assert "***" in record.msg

@pytest.mark.unit
class TestJSONFormatter:
    """测试 JSON 格式化器"""

    def test_json_formatter(self):
        """测试 JSON 格式化"""
        formatter = JSONFormatter(service_name="test-service", environment="test")
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        # 应该是有效的 JSON
        data = json.loads(result)

        assert data["service"] == "test-service"
        assert data["environment"] == "test"
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"

@pytest.mark.unit
class TestTextFormatter:
    """测试文本格式化器"""

    def test_text_formatter(self):
        """测试文本格式化"""
        formatter = TextFormatter(use_colors=False, include_request_id=False)
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = formatter.format(record)

        assert "Test message" in result
        assert "INFO" in result

@pytest.mark.unit
class TestSetupLogger:
    """测试设置日志器"""

    def test_setup_logger_basic(self):
        """测试基本日志器设置"""
        logger = setup_logger(
            name="test_logger",
            level="INFO",
            log_format="text",
            output="stdout",
        )

        assert logger is not None
        assert logger.level == logging.INFO
        assert len(logger.handlers) > 0

    def test_setup_logger_json(self):
        """测试 JSON 格式日志器"""
        logger = setup_logger(
            name="test_logger_json",
            level="DEBUG",
            log_format="json",
            output="stdout",
        )

        assert logger is not None
        # 应该有一个处理器
        assert len(logger.handlers) > 0

    def test_setup_logger_file_output(self):
        """测试文件输出"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"

            logger = setup_logger(
                name="test_logger_file",
                level="INFO",
                log_format="text",
                output="file",
                log_file=str(log_file),
            )

            logger.info("Test message")

            # 日志文件应该存在
            assert log_file.exists()

    def test_get_logger(self):
        """测试获取日志器"""
        logger = get_logger("test_get")

        assert logger is not None
        # 应该返回相同的日志器实例
        logger2 = get_logger("test_get")
        assert logger is logger2

@pytest.mark.unit
class TestRequestID:
    """测试请求 ID 功能"""

    def test_set_and_get_request_id(self):
        """测试设置和获取请求 ID"""
        set_request_id("req-12345")

        request_id = get_request_id()

        assert request_id == "req-12345"

    def test_clear_request_id(self):
        """测试清除请求 ID"""
        set_request_id("req-12345")
        set_request_id(None)

        request_id = get_request_id()

        assert request_id is None

@pytest.mark.unit
class TestLoggerContext:
    """测试日志器上下文管理器"""

    def test_logger_context(self):
        """测试日志器上下文"""
        set_request_id("original-id")

        with LoggerContext("context-id"):
            request_id = get_request_id()
            assert request_id == "context-id"

        # 退出上下文后应该恢复原始 ID
        request_id = get_request_id()
        assert request_id == "original-id"
