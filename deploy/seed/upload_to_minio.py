#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""上传种子文件到 MinIO"""
import os
import sys
from minio import Minio
from minio.error import S3Error

# MinIO 配置
MINIO_ENDPOINT = "minio:9000"
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
MINIO_BUCKET = "knowledgeflow"

# 种子文件列表
DOCS = [
    ("9001", "开发环境搭建SOP.md", "D:/The World/KnowledgeFlow-AI/deploy/seed/files/开发环境搭建SOP.md"),
    ("9002", "代码规范与评审流程.md", "D:/The World/KnowledgeFlow-AI/deploy/seed/files/代码规范与评审流程.md"),
    ("9003", "微服务架构设计文档.md", "D:/The World/KnowledgeFlow-AI/deploy/seed/files/微服务架构设计文档.md"),
    ("9004", "故障排查FAQ.md", "D:/The World/KnowledgeFlow-AI/deploy/seed/files/故障排查FAQ.md"),
    ("9005", "季度技术复盘.md", "D:/The World/KnowledgeFlow-AI/deploy/seed/files/季度技术复盘.md"),
]


def main():
    print("=== 上传种子文件到 MinIO ===\n")
    
    # 连接 MinIO
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False,
        )
        print(f"✓ 连接到 MinIO: {MINIO_ENDPOINT}")
    except Exception as e:
        print(f"✗ 连接 MinIO 失败: {e}")
        sys.exit(1)
    
    # 确保 bucket 存在
    try:
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            print(f"✓ 创建 bucket: {MINIO_BUCKET}")
        else:
            print(f"✓ Bucket 已存在: {MINIO_BUCKET}")
    except S3Error as e:
        print(f"✗ 创建 bucket 失败: {e}")
        sys.exit(1)
    
    # 上传文件
    for doc_id, filename, filepath in DOCS:
        if not os.path.exists(filepath):
            print(f"[SKIP] 文件不存在: {filename}")
            continue
        
        # 生成 object name: {kbId}/{uuid}.md
        object_name = f"1/{doc_id}.md"
        
        print(f"上传: {filename}")
        print(f"  本地: {filepath}")
        print(f"  MinIO: {MINIO_BUCKET}/{object_name}")
        
        try:
            client.fput_object(
                MINIO_BUCKET,
                object_name,
                filepath,
            )
            print(f"  ✓ 上传成功")
        except S3Error as e:
            print(f"  ✗ 上传失败: {e}")
        except Exception as e:
            print(f"  ✗ 异常: {e}")
    
    print("\n=== 完成 ===")
    print("提示：请刷新前端页面，验证文档预览功能")


if __name__ == "__main__":
    main()
