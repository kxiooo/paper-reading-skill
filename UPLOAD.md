# 上传到 GitHub（操作手册）

> 这个包已经排除了个人笔记、PDF、Obsidian 配置。目录总大小约 **0.2 MB**。
> 你只需要把它变成一个 Git 仓库，推到 GitHub。

---

## 0. 准备

- 注册 / 登录 [GitHub](https://github.com/)
- 安装二选一：
  - **GitHub Desktop**（推荐，图形界面，不用命令行）：https://desktop.github.com/
  - **Git for Windows**（命令行）：https://git-scm.com/download/win
- 建议先把本目录移到 vault 外面，例如 `E:\GitHub\paper-reading-skill\`，避免 Obsidian 扫描和嵌套仓库。

---

## 方式 A：GitHub Desktop（推荐）

1. 打开 GitHub Desktop → 登录 GitHub 账号。
2. 菜单 **File → Add local repository**。
3. 选择本目录（`paper-reading-skill`）。
4. 如果提示 "This directory does not appear to be a Git repository"，点 **create a repository**：
   - Name: `paper-reading-skill`
   - Description: `Obsidian + Claude Code 论文阅读知识库 Skill 包`
   - Local path: 指向本目录的**上一级**
   - 点 **Create repository**
5. 左下角填 commit message：`Initial commit: paper reading skill package`
6. 点 **Commit to main**。
7. 右上角 **Publish repository**：
   - 取消勾选 **Keep this code private**（要公开给同学用）
   - 点 **Publish repository**
8. 完成后点 **View on GitHub**，检查：
   - README 正常显示
   - 没有 PDF、没有 `_staging/notes/` 里的笔记

---

## 方式 B：命令行（Git Bash / PowerShell）

### 1. 进入目录

```bash
cd /e/GitHub/paper-reading-skill        # Git Bash
# 或 PowerShell: cd E:\GitHub\paper-reading-skill
```

### 2. 初始化并提交

```bash
git init -b main
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"

git add .
git status                              # ⚠️ 确认列表里没有 PDF / 个人笔记
git commit -m "Initial commit: paper reading skill package"
```

### 3. 在 GitHub 网页上建空仓库

- New repository → 名称 `paper-reading-skill`
- **不要**勾选 Add a README / .gitignore / license（本地已经有了）
- 创建后复制仓库地址，例如 `https://github.com/<你的用户名>/paper-reading-skill.git`

### 4. 关联并推送

```bash
git remote add origin https://github.com/<你的用户名>/paper-reading-skill.git
git push -u origin main
```

首次 push 会弹出登录窗口：
- 用浏览器登录 GitHub 即可（Git Credential Manager）
- 如果要求密码，**不能用账号密码**，要用 Personal Access Token：
  GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token，勾选 `repo`，用 token 当密码

---

## 推送后检查清单

- [ ] 仓库首页能看到 README
- [ ] 文件数约 40 个，体积 < 1 MB
- [ ] 没有 `*.pdf`
- [ ] `_staging/notes/` 里只有 `.gitkeep`
- [ ] `CLAUDE.md` 里没有你的姓名 / 私人项目
- [ ] 把仓库链接发给老师 / 同学，别人能直接 clone

---

## 以后更新

```bash
git add .
git commit -m "update: ..."
git push
```

或在 GitHub Desktop 里：改动会出现在左侧 → 填 message → **Commit to main** → **Push origin**。
