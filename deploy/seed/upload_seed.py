#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""通过后端 API 上传种子文件"""
import os
import sys
import urllib.request
import urllib.error

# 配置
API_BASE = "http://127.0.0.1:48080"
KB_ID = "1"
FILES_DIR = "D:/The World/KnowledgeFlow-AI/deploy/seed/files"

# 种子文件列表
DOCS = [
    ("9001", "开发环境搭建SOP.md"),
    ("9002", "代码规范与评审流程.md"),
    ("9003", "微服务架构设计文档.md"),
    ("9004", "故障排查FAQ.md"),
    ("9005", "季度技术复盘.md"),
]


def upload_file(filepath, kb_id, doc_id):
    """上传文件到后端 API"""
    filename = os.path.basename(filepath)
    
    # 构建 multipart/form-data
    boundary = f"----WebKitFormBoundary{doc_id}"
    with open(filepath, "rb") as f:
        file_content = f.read()
    
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="kbId"\r\n\r\n{kb_id}\r\n'
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: text/markdown\r\n\r\n"
    ).encode("utf-8") + file_content + f"\r\n--{boundary}--\r\n".encode("utf-8")
    
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "tenant-id": "1",
    }
    
    req = urllib.request.Request(
        f"{API_BASE}/admin-api/knowledge/document/upload",
        data=body,
        headers=headers,
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            import json
            result = json.loads(resp.read().decode("utf-8"))
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"  HTTP {e.code}: {error_body[:200]}")
        return None
    except Exception as e:
        print(f"  错误: {e}")
        return None


def main():
    print("=== 上传种子文件 ===\n")
    
    for doc_id, filename in DOCS:
        filepath = os.path.join(FILES_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"[SKIP] 文件不存在: {filename}")
            continue
        
        print(f"上传: {filename}")
        result = upload_file(filepath, KB_ID, doc_id)
        
        if result and result.get("code") == 0:
            data = result.get("data", {})
            print(f"  ✓ 成功: documentId={data.get('id')}, objectName={data.get('objectName')}")
        else:
            print(f"  ✗ 失败")
    
    print("\n=== 完成 ===")
    print("提示：请刷新前端页面，验证文档预览功能")


if __name__ == "__main__":
    main()
