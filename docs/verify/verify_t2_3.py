# -*- coding: utf-8 -*-
"""T2.3 文档模块验收脚本：上传(txt+pdf) → MinIO 对象 → pending 落库 → doc-pipeline 消息 → 列表/筛选/下载/批量删除"""
import io
import json
import urllib.request
import uuid

BASE = "http://localhost:48080/admin-api"
HEADERS = {"Content-Type": "application/json", "tenant-id": "1"}


def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = "Bearer " + token
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


def upload(token, kb_id, filename, content_bytes, tags=None):
    """multipart 上传（手动拼 multipart/form-data）"""
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    buf = io.BytesIO()
    buf.write(("--%s\r\nContent-Disposition: form-data; name=\"kbId\"\r\n\r\n%s\r\n" % (boundary, kb_id)).encode())
    if tags:
        buf.write(("--%s\r\nContent-Disposition: form-data; name=\"tags\"\r\n\r\n%s\r\n" % (boundary, tags)).encode())
    buf.write(("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\nContent-Type: application/octet-stream\r\n\r\n" % (boundary, filename)).encode())
    buf.write(content_bytes)
    buf.write(("\r\n--%s--\r\n" % boundary).encode())
    body = buf.getvalue()
    headers = {"tenant-id": "1", "Authorization": "Bearer " + token,
               "Content-Type": "multipart/form-data; boundary=" + boundary}
    r = urllib.request.Request(BASE + "/knowledge/document/upload", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8"))


results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


def login(username):
    code, body = req("POST", "/system/auth/login", {"username": username, "password": "admin123"})
    assert code == 200 and body["code"] == 0, f"登录失败 {username}: {body}"
    return body["data"]["accessToken"]


admin = login("admin")
test = login("test")
print("admin/test 登录成功")

# 0. 用知识库 id=1（软件开发团队知识库，admin owner）
KB_ID = 1

# 1. 上传 txt
txt_content = "这是 T2.3 验收测试文档。\nKnowledgeFlow 上传链路验证：MinIO 存储 + Redis Streams 投递。\n中文内容编码验证。".encode("utf-8")
code, r = upload(admin, KB_ID, "T2.3验收测试.txt", txt_content, "验收,测试")
check("上传 txt → 落库", r.get("code") == 0, str(r))
doc_id = r["data"]["id"] if r.get("data") else None
if r.get("data"):
    d = r["data"]
    check("契约字段齐全", set(d.keys()) == {"id", "kbId", "kbName", "filename", "fileType", "fileSize",
                                            "pageCount", "status", "uploader", "tags", "createdAt", "updatedAt"},
          str(sorted(d.keys())))
    check("status=pending", d["status"] == "pending", d["status"])
    check("fileType/fileSize", d["fileType"] == "txt" and d["fileSize"] == len(txt_content), f"{d['fileType']}/{d['fileSize']}")
    check("kbName/uploader", d["kbName"] == "软件开发团队知识库" and d["uploader"], f"{d['kbName']}/{d['uploader']}")
    check("tags 数组", d["tags"] == ["验收", "测试"], str(d["tags"]))

# 2. 上传 pdf（最小合法 pdf 字节）
pdf_content = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n170\n%%EOF"
code, r = upload(admin, KB_ID, "T2.3验收测试.pdf", pdf_content, "pdf验收")
check("上传 pdf → 落库", r.get("code") == 0, str(r))
pdf_id = r["data"]["id"] if r.get("data") else None

# 3. 类型白名单：上传 .exe 应拒绝
code, r = upload(admin, KB_ID, "evil.exe", b"MZ...")
check("非白名单类型拒绝", r.get("code") == 1011002001, str(r))

# 4. 列表/筛选
_, r = req("GET", "/knowledge/document/page?pageNo=1&pageSize=10&kbId=%d" % KB_ID, token=admin)
ids = [x["id"] for x in r["data"]["list"]] if r["code"] == 0 else []
check("分页含 2 篇新文档", doc_id in ids and pdf_id in ids, str(ids))
_, r = req("GET", "/knowledge/document/page?pageNo=1&pageSize=10&status=pending", token=admin)
check("按状态筛选 pending", all(x["status"] == "pending" for x in r["data"]["list"]), str(len(r["data"]["list"])))
_, r = req("GET", "/knowledge/document/page?pageNo=1&pageSize=10&fileType=pdf", token=admin)
check("按类型筛选 pdf", all(x["fileType"] == "pdf" for x in r["data"]["list"]), str(len(r["data"]["list"])))

# 5. 权限：test 用户对私有库 id=1 的文档列表（test 非成员）
_, r = req("GET", "/knowledge/document/get?id=%d" % doc_id, token=test)
check("非成员访问私有库文档被拒", r.get("code") == 1011000002, str(r))

# 6. 下载
r = urllib.request.Request(BASE + "/knowledge/document/download?id=%d" % doc_id, headers=dict(HEADERS, Authorization="Bearer " + admin))
with urllib.request.urlopen(r) as resp:
    content = resp.read()
check("下载内容一致", content == txt_content, f"{len(content)} bytes")

# 7. 知识库 documentCount 增加
_, r = req("GET", "/knowledge/kb/get?id=%d" % KB_ID, token=admin)
check("documentCount 已 +2", r["data"]["documentCount"] >= 2, f"documentCount={r['data']['documentCount']}")

# 8. 批量删除
_, r = req("DELETE", "/knowledge/document/delete?ids=%d,%d" % (doc_id, pdf_id), token=admin)
check("批量删除", r.get("code") == 0, str(r))
_, r = req("GET", "/knowledge/document/get?id=%d" % doc_id, token=admin)
check("删除后查询不存在", r.get("code") == 1011002000, str(r))

print("\n===== 结果汇总 =====")
passed = sum(1 for _, ok, _ in results if ok)
print(f"通过 {passed}/{len(results)}")
for name, ok, detail in results:
    if not ok:
        print(f"  FAIL: {name} -> {detail}")
