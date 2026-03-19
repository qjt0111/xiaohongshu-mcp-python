# 发布工作流参考

本文档描述小红书发布的详细流程，供 Skill 开发参考。

## 图文发布流程

1. 打开发布页面：`https://creator.xiaohongshu.com/publish/publish?target=image`
2. 上传图片（支持多张）
3. 填写标题（限制20字）
4. 填写正文
5. 填写标签（可选）
6. 设置可见范围（可选）
7. 点击发布按钮

## 视频发布流程

1. 打开发布页面：`https://creator.xiaohongshu.com/publish/publish?target=video`
2. 上传视频文件
3. 等待视频处理完成
4. 填写标题和正文
5. 点击发布

## 登录流程

1. 打开首页：`https://www.xiaohongshu.com/explore`
2. 检查是否存在登录按钮
3. 如果未登录，显示二维码供用户扫码
4. 登录成功后保存 cookies

## Cookies 管理

- 保存位置：`cookies.json`
- 环境变量：`COOKIES_PATH` 可自定义路径
- 删除 cookies 即可重置登录状态