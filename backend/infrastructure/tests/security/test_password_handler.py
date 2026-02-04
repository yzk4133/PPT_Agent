"""
Password Handler 测试
"""

import pytest
from infrastructure.security.password_handler import PasswordHandler
from infrastructure.exceptions.validation import PasswordValidationException

@pytest.mark.unit
class TestPasswordHandler:
    """测试 PasswordHandler 类"""

    def test_password_handler_initialization(self):
        """测试密码处理器初始化"""
        handler = PasswordHandler()

        assert handler.context is not None
        assert handler.MIN_LENGTH == 8
        assert handler.REQUIRE_UPPERCASE is True
        assert handler.REQUIRE_LOWERCASE is True
        assert handler.REQUIRE_DIGIT is True
        assert handler.REQUIRE_SPECIAL is False

    def test_hash_password(self):
        """测试密码哈希"""
        handler = PasswordHandler()

        plain_password = "TestPassword123"
        hashed = handler.hash_password(plain_password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != plain_password
        assert hashed.startswith("$2b$")  # bcrypt 哈希前缀

    def test_hash_password_different_each_time(self):
        """测试每次哈希结果不同"""
        handler = PasswordHandler()

        password = "TestPassword123"
        hash1 = handler.hash_password(password)
        hash2 = handler.hash_password(password)

        # bcrypt 每次生成不同的盐，所以哈希应该不同
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        handler = PasswordHandler()

        plain_password = "TestPassword123"
        hashed = handler.hash_password(plain_password)

        result = handler.verify_password(plain_password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        handler = PasswordHandler()

        plain_password = "TestPassword123"
        wrong_password = "WrongPassword123"
        hashed = handler.hash_password(plain_password)

        result = handler.verify_password(wrong_password, hashed)

        assert result is False

    def test_verify_password_empty(self):
        """测试验证空密码"""
        handler = PasswordHandler()

        hashed = handler.hash_password("TestPassword123")

        result = handler.verify_password("", hashed)

        assert result is False

    def test_validate_password_strength_valid(self):
        """测试验证有效密码强度"""
        handler = PasswordHandler()

        valid_passwords = [
            "Test1234",
            "MyP@ssw0rd",
            "SecurePass123",
            "Abcdefg123",
        ]

        for password in valid_passwords:
            is_valid, error_msg = handler.validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid: {error_msg}"
            assert error_msg == ""

    def test_validate_password_strength_too_short(self):
        """测试验证过短密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("Test12")

        assert is_valid is False
        assert "至少需要 8 个字符" in error_msg

    def test_validate_password_strength_no_uppercase(self):
        """测试验证无大写字母密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("testpassword123")

        assert is_valid is False
        assert "大写字母" in error_msg

    def test_validate_password_strength_no_lowercase(self):
        """测试验证无小写字母密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("TESTPASSWORD123")

        assert is_valid is False
        assert "小写字母" in error_msg

    def test_validate_password_strength_no_digit(self):
        """测试验证无数字密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("TestPassword")

        assert is_valid is False
        assert "数字" in error_msg

    def test_validate_password_strength_all_requirements(self):
        """测试验证所有要求都缺失的密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("short")

        assert is_valid is False
        # 应该至少报告长度问题

    def test_validate_and_hash_valid(self):
        """测试验证并加密有效密码"""
        handler = PasswordHandler()

        password = "TestPassword123"
        hashed = handler.validate_and_hash(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")

    def test_validate_and_hash_invalid(self):
        """测试验证并加密无效密码"""
        handler = PasswordHandler()

        with pytest.raises(PasswordValidationException):
            handler.validate_and_hash("short")

    def test_unicode_password(self):
        """测试 Unicode 密码"""
        handler = PasswordHandler()

        # 使用较短的 Unicode 密码以避免超过 72 字节限制
        password = "测试1A"  # 每个中文字符3字节 + 其他 = 约14字节
        hashed = handler.hash_password(password)

        result = handler.verify_password(password, hashed)

        assert result is True

    def test_very_long_password(self):
        """测试很长的密码"""
        handler = PasswordHandler()

        # bcrypt 限制密码最多72字节，使用70个字符
        password = "A" * 69 + "1"  # 70 个字符，在72字节限制内
        hashed = handler.hash_password(password)

        result = handler.verify_password(password, hashed)

        assert result is True

    def test_password_with_special_characters(self):
        """测试包含特殊字符的密码"""
        handler = PasswordHandler()

        passwords = [
            "Test!@#123",
            "P@ssw0rd!",
            "Secure#123Pass",
        ]

        for password in passwords:
            is_valid, error_msg = handler.validate_password_strength(password)
            assert is_valid is True, f"Password '{password}' should be valid: {error_msg}"

            hashed = handler.hash_password(password)
            result = handler.verify_password(password, hashed)
            assert result is True

@pytest.mark.unit
class TestPasswordHandlerEdgeCases:
    """测试 PasswordHandler 边界情况"""

    def test_exactly_min_length(self):
        """测试恰好是最小长度的密码"""
        handler = PasswordHandler()

        password = "Test1234"  # 8 个字符
        is_valid, error_msg = handler.validate_password_strength(password)

        assert is_valid is True
        assert error_msg == ""

    def test_one_less_than_min_length(self):
        """测试比最小长度少 1 的密码"""
        handler = PasswordHandler()

        password = "Test123"  # 7 个字符
        is_valid, error_msg = handler.validate_password_strength(password)

        assert is_valid is False

    def test_only_uppercase_and_digit(self):
        """测试只有大写和数字的密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("TEST1234")

        assert is_valid is False
        assert "小写字母" in error_msg

    def test_only_lowercase_and_digit(self):
        """测试只有小写和数字的密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("test1234")

        assert is_valid is False
        assert "大写字母" in error_msg

    def test_only_uppercase_and_lowercase(self):
        """测试只有大小写字母的密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("TestTest")

        assert is_valid is False
        assert "数字" in error_msg

    def test_common_passwords(self):
        """测试常见弱密码"""
        handler = PasswordHandler()

        weak_passwords = [
            "Password1",
            "Test1234",
            "Admin123",
        ]

        for password in weak_passwords:
            # 这些密码在技术上符合强度要求，但实际应用中可能需要额外检查
            is_valid, error_msg = handler.validate_password_strength(password)
            assert is_valid is True  # 基本强度验证通过

    def test_empty_password(self):
        """测试空密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("")

        assert is_valid is False

    def test_whitespace_only_password(self):
        """测试只有空格的密码"""
        handler = PasswordHandler()

        is_valid, error_msg = handler.validate_password_strength("        ")

        assert is_valid is False

@pytest.mark.unit
class TestPasswordHandlerSecurity:
    """测试密码处理安全特性"""

    def test_hash_timing_attack_resistance(self):
        """测试哈希对时序攻击的抵抗"""
        import time

        handler = PasswordHandler()

        password = "TestPassword123"
        hashed = handler.hash_password(password)

        # 测试正确密码的验证时间
        start = time.time()
        handler.verify_password(password, hashed)
        correct_time = time.time() - start

        # 测试错误密码的验证时间
        start = time.time()
        handler.verify_password("WrongPassword123", hashed)
        incorrect_time = time.time() - start

        # 时间应该大致相同（bcrypt 的恒定时间特性）
        # 允许较大的误差，因为系统负载可能影响
        ratio = max(correct_time, incorrect_time) / min(correct_time, incorrect_time)
        assert ratio < 10, "Timing difference too large, might be vulnerable to timing attacks"

    def test_hash_reversibility(self):
        """测试哈希不可逆"""
        handler = PasswordHandler()

        password = "TestPassword123"
        hashed = handler.hash_password(password)

        # 无法从哈希恢复原始密码
        assert password not in hashed

    def test_different_salts(self):
        """测试不同盐值"""
        handler = PasswordHandler()

        password = "TestPassword123"
        hash1 = handler.hash_password(password)
        hash2 = handler.hash_password(password)

        # 两个哈希应该不同（因为盐不同）
        assert hash1 != hash2

        # 但都应该能验证原密码
        assert handler.verify_password(password, hash1)
        assert handler.verify_password(password, hash2)
