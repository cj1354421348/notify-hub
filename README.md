# Notify Hub - 运行指南

![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)

## License
This project is licensed under the **GNU Affero General Public License v3.0 (AGPLv3)**.
See the [LICENSE](LICENSE) file for details.

## 环境要求
- Python 3.9+
- Node.js 16+
- PostgreSQL (远程或本地)

## 1. 后端设置 (Backend)

进入 `backend` 目录：
```bash
cd backend
```

安装依赖 (Phase 2 更新)：
```bash
pip install -r requirements.txt
# 包含新增的 python-jose, passlib, python-multipart
```

配置 `.env` 文件：
确保 `backend/.env` 中包含正确的 `DATABASE_URL`，以及新增的 `WEB_USERNAME` 和 `WEB_PASSWORD`。

启动 API 服务：
```bash
python backend/main.py
```

## 2. 前端设置 (Frontend)

进入 `frontend` 目录：
```bash
cd frontend
```

安装依赖 (Phase 2 更新)：
```bash
# 必须执行此命令以安装 Naive UI 和 Router
npm install naive-ui vfonts vue-router
npm install
```

启动开发服务器：
```bash
npm run dev
```

## 3. 验证 (Verification)

**测试 API**:
在后端启动后，新开一个终端运行测试脚本：
```bash
python backend/test_api.py
```

**访问界面**:
打开浏览器访问前端控制台显示的地址 (通常是 `http://localhost:5173`)。
