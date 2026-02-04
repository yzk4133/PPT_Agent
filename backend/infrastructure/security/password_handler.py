"""
密码处理
"""

from passlib.context import CryptContext
from infrastructure.exceptions.validation import PasswordValidationException

class PasswordHandler:
    """密码加密与验证"""

    # 密码强度要求
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = False

    def __init__(self):
        self.context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """
        加密密码

        Args:
            password: 明文密码

        Returns:
            加密后的密码
        """
        return self.context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        验证密码

        Args:
            plain_password: 明文密码
            hashed_password: 加密后的密码

        Returns:
            密码是否匹配
        """
        return self.context.verify(plain_password, hashed_password)

    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """
        验证密码强度

        Args:
            password: 密码

        Returns:
            (是否有效, 错误消息)
        """
        if len(password) < self.MIN_LENGTH:
            return False, f"密码长度至少需要 {self.MIN_LENGTH} 个字符"

        if self.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            return False, "密码必须包含至少一个大写字母"

        if self.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            return False, "密码必须包含至少一个小写字母"

        if self.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            return False, "密码必须包含至少一个数字"

        if self.REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                return False, "密码必须包含至少一个特殊字符"

        return True, ""

    def validate_and_hash(self, password: str) -> str:
        """
        验证密码强度并加密

        Args:
            password: 明文密码

        Returns:
            加密后的密码

        Raises:
            PasswordValidationException: 密码不符合强度要求
        """
        is_valid, error_msg = self.validate_password_strength(password)
        if not is_valid:
            raise PasswordValidationException(error_msg)

        return self.hash_password(password)

# 全局实例
password_handler = PasswordHandler()
