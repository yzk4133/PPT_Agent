# 贡献指南

感谢您对MultiAgent PPT项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告问题

如果您发现了bug或有功能建议：

1. 检查[Issues](../../issues)是否已有相同问题
2. 如果没有，创建新Issue，包含：
   - 清晰的标题
   - 详细的问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（操作系统、Python版本等）

### 提交代码

#### 1. Fork项目

点击右上角的Fork按钮

#### 2. 克隆到本地

```bash
git clone https://github.com/your-username/MultiAgentPPT.git
cd MultiAgentPPT
```

#### 3. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

分支命名规范：
- `feature/` - 新功能
- `fix/` - bug修复
- `docs/` - 文档更新
- `refactor/` - 代码重构
- `test/` - 测试相关

#### 4. 编写代码

- 遵循现有代码风格
- 添加必要的注释
- 更新相关文档
- 确保代码通过所有测试

#### 5. 提交更改

```bash
git add .
git commit -m "feat: 添加某某功能

- 实现了XXX功能
- 添加了单元测试
- 更新了README

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

提交信息格式：
- `feat:` 新功能
- `fix:` bug修复
- `docs:` 文档更新
- `style:` 代码格式
- `refactor:` 重构
- `test:` 测试
- `chore:` 构建/工具

#### 6. 推送分支

```bash
git push origin feature/your-feature-name
```

#### 7. 创建Pull Request

1. 访问您的fork页面
2. 点击"New Pull Request"
3. 填写PR模板
4. 等待代码审查

## 代码规范

### Python代码风格

- 使用[Black](https://black.readthedocs.io/)进行格式化
- 使用[isort](https://pycqa.github.io/isort/)排序导入
- 遵循[PEP 8](https://pep8.org/)
- 添加类型提示（Type Hints）
- 编写文档字符串（Docstrings）

```bash
# 格式化代码
black backend/
isort backend/

# 检查代码质量
flake8 backend/
mypy backend/
```

### 前端代码风格

- 使用[ESLint](https://eslint.org/)
- 使用[Prettier](https://prettier.io/)
- 遵循Airbnb风格指南

```bash
# 格式化代码
npm run format

# 检查代码
npm run lint
```

## 测试

### 运行测试

```bash
# 后端测试
pytest backend/tests/

# 前端测试
npm test

# 覆盖率测试
pytest --cov=backend --cov-report=html
```

### 编写测试

- 为新功能添加单元测试
- 确保测试覆盖率不低于80%
- 使用清晰的测试名称

## 文档

- 保持文档更新
- 使用清晰的中文说明
- 添加代码示例
- 更新CHANGELOG

## 设计原则

1. **简洁性**: 代码应简洁明了
2. **可维护性**: 易于理解和修改
3. **可测试性**: 便于编写测试
4. **性能**: 考虑性能影响
5. **安全性**: 注意安全问题

## 获得帮助

- 查看[文档](../../docs)
- 在[Discussions](../../discussions)中提问
- 加入我们的社区

## 行为准则

- 尊重所有贡献者
- 欢迎新手提问
- 建设性的反馈
- 专注于项目目标

## 许可证

贡献的代码将采用MIT许可证。

感谢您的贡献！
