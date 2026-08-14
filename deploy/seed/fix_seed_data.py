#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复种子数据：通过后端 API 上传文件到 MinIO

使用后端 /admin-api/knowledge/document/upload 接口上传种子文件。
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

# 后端 API 配置
API_BASE = "http://backend:48080"
KB_ID = "1"

# 文档 id 和文件名映射
DOCS = [
    (9001, "开发环境搭建SOP.md"),
    (9002, "代码规范与评审流程.md"),
    (9003, "微服务架构设计文档.md"),
    (9004, "故障排查FAQ.md"),
    (9005, "季度技术复盘.md"),
]

SEED_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_DIR = os.path.join(SEED_DIR, "files")


def upload_via_api(filepath: str, kb_id: str) -> dict:
    """通过后端 API 上传文件"""
    # 读取文件内容
    with open(filepath, "rb") as f:
        file_content = f.read()

    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1]

    # 构建 multipart/form-data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="kbId"\r\n\r\n{kb_id}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("utf-8") + file_content + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "tenant-id": "1",
        "Authorization": "Bearer test-token",  # mock 模式不需要真实 token
    }

    req = urllib.request.Request(
        f"{API_BASE}/admin-api/knowledge/document/upload",
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body[:200]}")
    except Exception as e:
        raise RuntimeError(f"上传失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="修复种子数据")
    args = parser.parse_args()

    print(f"== 修复种子数据：{FILES_DIR} ==")
    print()

    if not os.path.exists(FILES_DIR):
        print(f"错误：文件目录不存在: {FILES_DIR}")
        sys.exit(1)

    for doc_id, filename in DOCS:
        filepath = os.path.join(FILES_DIR, filename)

        if not os.path.exists(filepath):
            print(f"[SKIP] 文件缺失: {filename}")
            continue

        print(f"处理 {filename}...")

        try:
            # 上传文件
            result = upload_via_api(filepath, KB_ID)

            if result.get("code") == 0:
                data = result.get("data", {})
                print(f"  ✓ 上传成功: documentId={data.get('id')}, objectName={data.get('objectName')}")
            else:
                print(f"  ✗ 上传失败: {result.get('message')}")
        except Exception as e:
            print(f"  ✗ 异常: {e}")
            continue

    print()
    print("== 修复完成 ==")
    print("提示：请刷新前端页面，验证文档预览功能")


if __name__ == "__main__":
    main()
