# 持久化记忆系统 - 快速启动

## 一键设置（推荐）

```powershell
# 进入persistent_memory目录
cd backend/persistent_memory

# 安装依赖
pip install -r requirements.txt

# 运行设置向导
python setup.py
```

设置向导会自动完成：

1. ✅ 启动 PostgreSQL 和 Redis 服务
2. ✅ 初始化数据库表和索引
3. ✅ 执行系统健康检查

---

## 手动设置

### 步骤1: 启动数据库服务

```powershell
cd backend
docker-compose up -d postgres redis
```

等待20秒让服务完全启动。

### 步骤2: 初始化数据库

```powershell
cd persistent_memory
python database.py --init
```

### 步骤3: 配置环境变量

```powershell
# 复制模板
cp ../env_template_memory ../slide_agent/.env

# 编辑 .env 文件，填入:
# - USE_PERSISTENT_MEMORY=true
# - OPENAI_API_KEY=your_key_here
```

### 步骤4: 启动Agent

```powershell
cd ..
docker-compose up -d ppt_agent ppt_outline
```

---

## 验证安装

```powershell
# 检查数据库健康
python database.py --health

# 查看服务日志
docker-compose logs -f postgres redis

# 测试连接
docker exec -it multiagent_postgres psql -U postgres -d multiagent_ppt
```

---

## 故障排查

### PostgreSQL未启动

```powershell
docker-compose restart postgres
docker logs multiagent_postgres
```

### Redis连接失败

```powershell
docker exec -it multiagent_redis redis-cli ping
# 应返回: PONG
```

### 向量服务不可用

检查 `.env` 文件中的 `OPENAI_API_KEY` 是否配置正确。

---

查看完整文档: [README.md](README.md)
