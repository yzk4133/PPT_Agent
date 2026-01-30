# Dockerfile

FROM node:22-alpine

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories

WORKDIR /app
RUN apk update
RUN apk add --no-cache openssl

COPY . .

ENV DATABASE_URL=postgresql://postgres:welcome@localhost:5432/presentation_ai
ENV A2A_AGENT_OUTLINE_URL=http://127.0.0.1:10001
ENV A2A_AGENT_SLIDES_URL=http://127.0.0.1:10012

# RUN npm install -g pnpm

RUN npm install -g pnpm --registry=https://registry.npmmirror.com
# 设置 pnpm 的源
RUN pnpm config set registry https://registry.npmmirror.com

RUN pnpm install
# 正式环境才build
RUN pnpm build
# 正式环境才build
RUN pnpm build

EXPOSE 3000

CMD ["pnpm", "start"]
