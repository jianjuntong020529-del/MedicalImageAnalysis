# Git 分支管理与操作规范说明
## 一、概述
本文档适用于 MedicalImageAnalysisSoftwarev1.0 项目，规范 Git 分支的创建、切换、提交、合并等操作流程，以及常见异常处理方案，确保团队协作高效、代码版本可控。

## 二、分支基础操作
### 2.1 分支核心概念
- **主分支**：`master`/`main`（生产环境代码）、`develop`（开发主分支）
- **功能分支**：基于主分支创建，用于单个功能/修复开发（如 `adjust-page`、`fix-login-bug`）
- **命名规范**：`类型-功能描述`（小写+短横线），例如：
  - 功能开发：`feature-xxx`
  - 页面调整：`adjust-page-layout`
  - Bug 修复：`fix-xxx-error`
  - 紧急修复：`hotfix-xxx`

### 2.2 分支创建与切换
#### （1）创建分支（Windows PowerShell/Linux 通用）
```bash
# 方式1：分步创建（新手友好）
git branch 分支名  # 如：git branch adjust-page

# 方式2：创建并立即切换（推荐）
git checkout -b 分支名  # 如：git checkout -b adjust-page
```

#### （2）切换分支
```bash
# 切换到已存在的分支
git checkout 分支名  # 如：git checkout master
```

#### （3）查看分支
```bash
# 查看本地所有分支（* 标记当前分支）
git branch

# 查看本地+远程所有分支
git branch -a

# 查看远程分支
git branch -r
```

#### （4）推送分支到远程（多人协作必备）
```bash
# 推送本地分支到远程，并设置上游跟踪（-u 仅首次需要）
git push -u origin 分支名  # 如：git push -u origin adjust-page

# 后续推送分支修改（无需指定参数）
git push
```

#### （5）删除分支
```bash
# 删除本地分支（需先切换到其他分支）
git branch -d 分支名  # 如：git branch -d adjust-page

# 强制删除未合并的本地分支
git branch -D 分支名

# 删除远程分支
git push origin --delete 分支名
```

## 三、分支提交规范
### 3.1 提交前准备
```bash
# 1. 查看修改的文件
git status

# 2. 添加修改到暂存区（可选指定文件，推荐用 . 全选）
git add 文件名  # 单个文件：git add src/page/index.py
git add .       # 所有修改文件
```

### 3.2 提交信息规范
#### （1）提交信息格式
```bash
git commit -m "分支类型: 具体修改描述"
```
#### （2）规范示例
| 分支类型 | 场景                | 提交信息示例                          |
|----------|---------------------|---------------------------------------|
| adjust   | 页面调整            | `adjust-page: 优化XX页面布局`         |
| feature  | 新功能开发          | `feature-login: 实现用户登录验证逻辑` |
| fix      | Bug 修复            | `fix-page: 修复XX页面样式错位问题`    |
| hotfix   | 生产环境紧急修复    | `hotfix-api: 修复接口返回数据异常`    |
| init     | 分支初始化          | `init: 创建adjust-page分支`           |

#### （3）提交要求
- 描述简洁明了，不超过 50 个字；
- 用中文描述，精准体现修改内容；
- 避免无意义提交（如 `update`/`modify`/`fix bug`）。

### 3.3 拉取远程最新代码（避免冲突）
```bash
# 切换到目标分支后，拉取远程最新代码
git pull origin 分支名  # 如：git pull origin adjust-page
```

## 四、分支合并流程
### 4.1 功能完成后合并到主分支（以 master 为例）
```bash
# 1. 切换到主分支
git checkout master

# 2. 拉取主分支最新代码（关键：避免合并冲突）
git pull origin master

# 3. 合并功能分支到主分支
git merge 功能分支名  # 如：git merge adjust-page

# 4. 推送合并后的代码到远程主分支
git push origin master
```

### 4.2 解决合并冲突
#### （1）冲突表现
合并时 Git 提示 `Automatic merge failed; fix conflicts and then commit the result`，并标记冲突文件。

#### （2）解决步骤
1. 打开冲突文件，找到 `<<<<<<< HEAD`/`=======`/`>>>>>>> 分支名` 标记的冲突区域；
2. 手动修改冲突内容（保留正确代码，删除冲突标记）；
3. 提交解决后的代码：
   ```bash
   git add 冲突文件名
   git commit -m "fix: 解决adjust-page合并到master的冲突"
   git push origin master
   ```

## 五、常见异常处理
### 5.1 锁文件冲突（index.lock）
#### （1）报错信息
```
Unable to create 'xxx/.git/index.lock': File exists. Another git process seems to be running...
```
#### （2）解决方案
```bash
# Windows PowerShell
if (Test-Path .git\index.lock) {
    Remove-Item -Force .git\index.lock
}

# Linux/Mac
rm -rf .git/index.lock
```

### 5.2 推送分支提示 “refspec 不匹配”
#### （1）报错信息
```
error: src refspec 分支名 does not match any
error: failed to push some refs to '远程仓库地址'
```
#### （2）解决方案
1. 检查分支名是否输入正确（区分大小写）；
2. 确保分支有至少 1 次提交记录：
   ```bash
   git add .
   git commit -m "init: 初始化分支提交"
   git push -u origin 分支名
   ```
3. 检查远程仓库地址是否正确：
   ```bash
   git remote -v  # 查看远程仓库关联
   git remote set-url origin 正确仓库地址  # 修正地址
   ```

### 5.3 本地分支落后于远程分支
#### （1）报错信息
```
hint: Updates were rejected because the tip of your current branch is behind
```
#### （2）解决方案
```bash
# 拉取远程最新代码并合并
git pull origin 分支名

# 若合并冲突，解决后重新推送
git add .
git commit -m "fix: 合并远程代码冲突"
git push origin 分支名
```

### 5.4 .pyc/pycache 冲突
#### （1）问题原因
Python 编译文件被 Git 追踪，导致合并/推送冲突。
#### （2）解决方案
1. 在项目根目录创建/修改 `.gitignore` 文件，添加忽略规则：
   ```
   # Python 编译文件
   __pycache__/
   *.pyc
   *.pyo
   *.pyd
   ```
2. 移除已追踪的编译文件：
   ```bash
   git rm -r --cached **/__pycache__
   git rm -r --cached **/*.pyc
   git add .gitignore
   git commit -m "feat: 添加pycache/pyc文件忽略规则"
   git push
   ```

## 六、总结
1. **分支管理核心**：功能开发在独立分支进行，避免直接修改主分支；
2. **提交规范**：提交信息需体现分支类型+具体修改，便于追溯；
3. **异常处理**：锁文件冲突删除 `index.lock`，分支推送失败先检查提交记录，编译文件冲突通过 `.gitignore` 解决；
4. **协作原则**：多人开发同一分支时，每次开发前先 `git pull` 拉取最新代码，减少冲突。

## Gitee账号和GitHub账号
```bash
# Gitee
git config --global user.name '童建军' 
git config --global user.email '2691206891@qq.com'
```

```bash
# GitHub
git config --global user.name "jianjuntong020529-del"
git config --global user.email "Dezz020529.."

```