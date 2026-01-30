# ALLWEONE® AI 演示文稿生成器（Gamma 替代品）

⭐ 帮助我们让更多开发者了解并壮大 ALLWEONE 社区，为本仓库点个 Star！

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)

一个受 gamma.app 启发的开源 AI 演示文稿生成器，能用 AI 快速生成精美幻灯片，并可自定义。该工具是 ALLWEONE AI 平台的一部分。

[在线演示](https://allweone.com/presentations) | [视频教程](https://www.youtube.com/watch?v=UUePLJeFqVQ)

---

## 🌟 功能亮点

- **AI 内容生成**：用 AI 一键生成任意主题的完整演示文稿
- **自定义幻灯片**：可选择幻灯片数量、语言和页面风格
- **可编辑大纲**：生成后可审阅和修改大纲
- **多主题支持**：内置 9 种主题，更多主题即将上线
- **自定义主题**：可从零创建并保存自己的主题
- **图片生成**：可选不同 AI 图片生成模型为幻灯片配图
- **受众风格选择**：支持专业/休闲两种演示风格
- **实时生成**：演示文稿内容实时生成可见
- **完全可编辑**：可修改文本、字体和设计元素
- **演示模式**：可直接在应用内放映演示文稿
- **自动保存**：编辑内容自动保存

---

## 🚀 快速开始

### 前置条件

- Node.js 18.x 或更高版本
- npm 或 yarn
- OpenAI API Key（用于 AI 生成）
- Together AI API Key（用于图片生成）
- Google Client ID 和 Secret（用于认证功能）

### 安装步骤

**0. 安装 Docker PostgreSQL**

**使用 VPN 时：**
```bash
docker run --name postgresdb -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=welcome -d postgres
```

**国内使用（镜像加速）：**
```bash
docker run --name postgresdb -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=welcome -d swr.cn-north-4.myhuaweicloud.com/ddn-k8s/ghcr.io/cloudnative-pg/postgresql:15
```

**1. 安装依赖**

在 frontend 目录下：

```bash
cp env_template .env
npm install -g pnpm
pnpm install
```

**2. 设置数据库**

```bash
pnpm db:push
```

**3. 插入默认用户数据**

以前有用户认证，现已删除，使用一条默认用户测试：

```sql
INSERT INTO public."User" (
    "id", "name", "email", "password", "emailVerified", "image",
    "headline", "bio", "interests", "location", "website", "role", "hasAccess"
) VALUES (
    '01', 'Admin User', 'admin@example.com', 'hashed_password_here', NOW(), NULL,
    'Administrator', 'Default admin account', ARRAY['admin', 'manager'],
    'Global', 'https://example.com', 'ADMIN', true
);
```

**4. 检查 .env 文件**

```bash
cp env_template .env
```

配置示例：

```env
DATABASE_URL="postgresql://postgres:welcome@localhost:5432/presentation_ai"
A2A_AGENT_OUTLINE_URL="http://localhost:10001"
A2A_AGENT_SLIDES_URL="http://localhost:10011"
# 下载成ppt的后端
DOWNLOAD_SLIDES_URL="http://localhost:10021"
```

**5. 启动开发服务器**

```bash
pnpm dev
```

**6. 在浏览器中打开**

[http://localhost:3000](http://localhost:3000) 查看应用。

---

## 💻 使用指南

### 创建演示文稿

1. 进入仪表板
2. 输入演示文稿主题
3. 选择幻灯片数量（推荐：5-10）
4. 选择您偏好的语言
5. 选择页面风格
6. 点击"生成大纲"
7. 审阅并编辑 AI 生成的大纲
8. 为演示文稿选择一个主题
9. 选择图像生成模型
10. 选择您的演示风格（专业/休闲）
11. 点击"生成演示文稿"
12. 等待 AI 实时创建幻灯片
13. 根据需要预览、编辑和完善演示文稿
14. 直接从应用中演示或导出演示文稿

### 自定义主题

1. 点击"创建新主题"
2. 从头开始或从现有主题派生
3. 自定义颜色、字体和布局
4. 保存您的主题以供将来使用

---

## 🧰 技术栈

该项目使用以下技术构建：

- **Next.js**：用于服务器渲染应用的 React 框架
- **React**：构建用户界面的 UI 库
- **Prisma**：带有 PostgreSQL 的数据库 ORM
- **Tailwind CSS**：实用优先的 CSS 框架
- **TypeScript**：带类型的 JavaScript
- **OpenAI API**：用于 AI 内容生成
- **Radix UI**：无头 UI 组件
- **Plate Editor**：用于处理文本、图像和幻灯片组件的富文本编辑系统
- **身份验证**：NextAuth.js 用于用户身份验证
- **UploadThing**：文件上传
- **DND Kit**：拖放功能

---

## 🛠️ 项目结构

```text
presentation/
├── .next/               # Next.js 构建输出
├── node_modules/        # 依赖
├── prisma/              # 数据库模式
│   └── schema.prisma    # Prisma 数据库模型
├── src/                 # 源代码
│   ├── app/             # Next.js 应用路由
│   ├── components/      # 可重用的 UI 组件
│   │   ├── auth/        # 身份验证组件
│   │   ├── presentation/  # 演示文稿相关组件
│   │   │   ├── dashboard/   # 仪表板 UI
│   │   │   ├── editor/      # 演示文稿编辑器
│   │   │   ├── outline/     # 演示文稿大纲组件
│   │   │   ├── theme/       # 主题相关组件
│   │   │   └── utils/       # 演示文稿工具
│   │   ├── prose-mirror/  # ProseMirror 编辑器组件
│   │   ├── text-editor/   # 文本编辑器组件
│   │   └── ui/           # 共享 UI 组件
│   ├── hooks/           # 自定义 React 钩子
│   ├── lib/             # 工具函数和共享代码
│   ├── provider/        # 上下文提供者
│   ├── server/          # 服务器端代码
│   └── states/          # 状态管理
├── .env                 # 环境变量
├── .env.example         # 示例环境变量
├── next.config.js       # Next.js 配置
├── package.json         # 项目依赖和脚本
├── tailwind.config.ts   # Tailwind CSS 配置
└── tsconfig.json        # TypeScript 配置
```

---

## 🤝 贡献代码

我们欢迎您为 ALLWEONE 演示文稿生成器贡献代码！以下是您可以帮助的方式：

1. Fork 本仓库
2. 创建一个特性分支（`git checkout -b feature/amazing-feature`）
3. 提交您的更改（`git commit -m 'Add some amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 提交一个 Pull Request

由 ALLWEONE™ 团队 ❤️ 打造 🇺🇸🇧🇷🇳🇵🇮🇳🇨🇳🇯🇵🇸🇬🇩🇪🏴🇺🇦🇰🇿🇷🇺🇦🇪🇸🇦🇰🇷🇹🇭🇮🇩🇲🇽🇬🇹🇫🇷🇮🇱🇻🇳🇵🇹🇮🇹🇨🇱🇨🇦🇵🇰🇸🇪🇱🇧

如有任何问题或支持，请在 GitHub 上提交问题或通过 Discord 联系我们 https://discord.gg/wSVNudUBdY

---

## 📡 API 接口说明

### 生成 PPT 大纲

**生成 PPT 内容：** `src/components/presentation/dashboard/PresentationGenerationManager.tsx`

**API 端点：** `/api/presentation/outline`

**请求示例：**

```bash
curl 'http://localhost:3000/api/presentation/outline' \
  -H 'Content-Type: application/json' \
  --data-raw '{"prompt":"xiao mi Car","numberOfCards":10,"language":"en-US"}'
```

---

## 📄 PPT 的 XML 示例格式内容

<details>
<summary>点击展开查看 XML 格式示例</summary>

```xml
<PRESENTATION>

<SECTION layout="vertical">
  <H1>AI in Education</H1>
  <P>Discover how artificial intelligence is transforming the educational landscape.</P>
  <IMG query="students engaging with AI technology in a modern classroom" />
</SECTION>

<SECTION layout="left">
  <H2>Benefits for Teachers and Students</H2>
  <BULLETS>
    <DIV>
      <H3>Personalized Learning</H3>
      <P>AI systems analyze student performance data to tailor educational content.</P>
    </DIV>
    <DIV>
      <H3>Efficiency in Administration</H3>
      <P>Teachers can automate grading and administrative tasks.</P>
    </DIV>
  </BULLETS>
  <IMG query="diverse students using AI software" />
</SECTION>

</PRESENTATION>
```

</details>

---

## 🔧 模拟生成大纲 - toDataStreamResponse 格式

<details>
<summary>点击展开查看代码示例</summary>

```typescript
import { LangChainAdapter } from "ai";
import { NextResponse } from "next/server";

interface SlidesRequest {
  title: string;
  outline: string[];
  language: string;
  tone: string;
}

// Helper function to convert an async string iterator to a ReadableStream
function iteratorToStream(iterator: AsyncGenerator<string>): ReadableStream<string> {
  return new ReadableStream({
    async pull(controller) {
      const { value, done } = await iterator.next();
      if (done) {
        controller.close();
      } else {
        controller.enqueue(value);
      }
    },
  });
}

export async function POST(req: Request) {
  try {
    const { title, outline, language, tone } = (await req.json()) as SlidesRequest;

    if (!title || !outline || !Array.isArray(outline) || !language) {
      return NextResponse.json(
        { error: "Missing required fields" },
        { status: 400 },
      );
    }

    const stream = iteratorToStream(customTextStream());
    return LangChainAdapter.toDataStreamResponse(stream);

  } catch (error) {
    console.error("Error in presentation generation:", error);
    return NextResponse.json(
      { error: "Failed to generate presentation slides" },
      { status: 500 },
    );
  }
}
```

</details>

---

## 🔍 解析模型的返回数据流

**解析函数位置：** `src/components/presentation/utils/parser.ts` 中的 `parseChunk` 函数
