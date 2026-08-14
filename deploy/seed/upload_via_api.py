#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传种子文件到后端 API（带租户 ID）"""
import os
import sys
import json
import urllib.request
import urllib.error

# 配置
API_BASE = "http://127.0.0.1:48080"
KB_ID = "1"
TENANT_ID = "1"
FILES_DIR = "D:/The World/KnowledgeFlow-AI/deploy/seed/files"

# 种子文件列表
DOCS = [
    ("9001", "开发环境搭建SOP.md"),
    ("9002", "代码规范与评审流程.md"),
    ("9003", "微服务架构设计文档.md"),
    ("9004", "故障排查FAQ.md"),
    ("9005", "季度技术复盘.md"),
]


def login(username, password, tenant_id):
    """登录获取 token"""
    body = json.dumps({"username": username, "password": password}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "tenant-id": tenant_id,
    }
    req = urllib.request.Request(
        f"{API_BASE}/admin-api/system/auth/login",
        data=body,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                return result.get("data", {}).get("accessToken", "")
            else:
                print(f"登录失败: {result.get('message')}")
                return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None


def upload_file(filepath, kb_id, token, tenant_id):
    """上传文件到后端 API"""
    filename = os.path.basename(filepath)
    
    # 构建 multipart/form-data
    boundary = f"----WebKitFormBoundary{os.urandom(16).hex()}"
    
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
        "tenant-id": tenant_id,
        "Authorization": f"Bearer {token}",
    }
    
    req = urllib.request.Request(
        f"{API_BASE}/admin-api/knowledge/document/upload",
        data=body,
        headers=headers,
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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
    
    # 登录
    token = login("admin", "admin123", TENANT_ID)
    if not token:
        print("无法获取 token，上传失败")
        sys.exit(1)
    
    print(f"✓ 登录成功")
    print()
    
    # 上传文件
    for doc_id, filename in DOCS:
        filepath = os.path.join(FILES_DIR, filename)
        
        if not os.path.exists(filepath):
            print(f"[SKIP] 文件不存在: {filename}")
            continue
        
        print(f"上传: {filename}")
        result = upload_file(filepath, KB_ID, token, TENANT_ID)
        
        if result and result.get("code") == 0:
            data = result.get("data", {})
            print(f"  ✓ 成功: documentId={data.get('id')}, objectName={data.get('objectName')}")
        else:
            print(f"  ✗ 失败")
    
    print("\n=== 完成 ===")


if __name__ == "__main__":
    main()
