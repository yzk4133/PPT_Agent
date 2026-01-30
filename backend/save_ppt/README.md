# 📁 PPT 保存接口服务

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 🚀 启动服务

```bash
python main_api.py
```

服务将启动 API 接口，方便前端调用保存 PPT 功能。

## 🔍 查看母版占位符

打印 PPT 母版的占位符信息（注意：占位符必须是 `placeholder` 类型，其它文本框类型不可用）：

```bash
python look_master.py
```

## 📝 功能说明

该服务提供以下功能：
- 接收前端传递的 JSON 格式 PPT 数据
- 使用 python-pptx 库将数据渲染到 PPT 母版
- 生成并返回可供下载的 .pptx 文件
