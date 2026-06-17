# 主题切换 + UI 现代化设计

## 概述

为 v2man 管理面板添加白天/黑夜双主题切换功能，并整体优化视觉风格为现代圆润风。

## 主题系统

### 技术方案

CSS 自定义属性（变量）+ 类切换：

- `:root` 定义深色主题变量，`.light` 定义浅色主题变量
- `theme.css` 全局导入，所有组件通过 `var(--xxx)` 引用
- 切换按钮在 AppLayout header 中，存 `localStorage`
- `<html>` 元素加 `.light` 类，全局 `transition` 实现平滑切换

### 配色变量

| 变量 | 深色值 | 浅色值 |
|------|--------|--------|
| `--bg-primary` | `#0f172a` | `#f8fafc` |
| `--bg-secondary` | `#1e293b` | `#f1f5f9` |
| `--bg-card` | `rgba(30,41,59,0.7)` | `#ffffff` |
| `--text-primary` | `#f1f5f9` | `#1e293b` |
| `--text-secondary` | `#94a3b8` | `#64748b` |
| `--text-muted` | `#64748b` | `#94a3b8` |
| `--accent` | `#3b82f6` | `#2563eb` |
| `--accent-gradient` | `linear-gradient(135deg,#3b82f6,#8b5cf6)` | 同 |
| `--border` | `rgba(59,130,246,0.15)` | `#e2e8f0` |
| `--success` | `#22c55e` | `#16a34a` |
| `--warning` | `#f59e0b` | `#d97706` |
| `--danger` | `#ef4444` | `#dc2626` |
| `--shadow` | `0 4px 24px rgba(0,0,0,0.3)` | `0 2px 12px rgba(0,0,0,0.08)` |

### 跟随系统

首屏检测 `prefers-color-scheme`，用户手动切换后覆盖并持久化。

## UI 优化

### 卡片

- `border-radius: 12px`
- 深色：`backdrop-filter: blur(12px)`，半透明背景，微发光边框
- 浅色：白色背景，柔和阴影，干净边框
- 悬停提升效果

### 导航

- 当前项渐变背景 `--accent-gradient`
- 图标/文字间距优化
- hover 背景过渡

### 按钮

- 主按钮渐变背景
- hover 轻微上浮 (`translateY(-1px)`)
- 过渡动画

### 进度条

- 渐变填充
- 圆角端点

### 表格

- 交替行背景
- 更清晰的分隔线
- 圆角容器

### 全局

- `box-sizing: border-box`
- 抗锯齿字体
- 平滑滚动
- 主题切换 0.3s 过渡

## 涉及文件

- `web/src/assets/theme.css` — 新增
- `web/src/main.ts` — 导入 theme.css
- `web/src/views/AppLayout.vue` — 主题切换按钮 + CSS 变量
- 所有 10 个页面组件 — 硬编码颜色替换为 CSS 变量
- `web/src/views/Login.vue`, `Register.vue` — 同步适配
