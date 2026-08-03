# -*- coding: utf-8 -*-
"""T2.2 知识库模块验收脚本（UTF-8 原生请求，避免终端编码问题）"""
import json
import urllib.request

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


def login(username):
    code, body = req("POST", "/system/auth/login", {"username": username, "password": "admin123"})
    assert code == 200 and body["code"] == 0, f"登录失败 {username}: {body}"
    return body["data"]["accessToken"]


results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")


admin = login("admin")
test = login("test")
print(f"admin/test 登录成功")

# 0. 清理上次残留的验收测试数据（幂等）
def cleanup():
    _, r = req("GET", "/knowledge/kb/list", token=admin)
    if r["code"] == 0:
        for kb in r["data"]:
            if kb["name"].startswith("验收测试"):
                _, page = req("GET", f"/knowledge/kb-member/page?kbId={kb['id']}", token=admin)
                if page["code"] == 0:
                    for m in page["data"]["list"]:
                        req("DELETE", f"/knowledge/kb-member/delete?id={m['id']}", token=admin)
                req("DELETE", f"/knowledge/kb/delete?id={kb['id']}", token=admin)
                print(f"清理残留: {kb['name']} (id={kb['id']})")
cleanup()

# 1. 创建私有库
_, r = req("POST", "/knowledge/kb/create", {"name": "验收测试-私有库", "description": "权限验证用", "isPrivate": True}, admin)
check("创建私有库", r["code"] == 0, str(r))
private_id = r.get("data")
# 2. 创建共享库
_, r = req("POST", "/knowledge/kb/create", {"name": "验收测试-共享库", "description": "共享可见", "isPrivate": False}, admin)
check("创建共享库", r["code"] == 0, str(r))
shared_id = r.get("data")

# 3. 名称查重
_, r = req("POST", "/knowledge/kb/create", {"name": "验收测试-私有库", "isPrivate": True}, admin)
check("名称重复拒绝", r["code"] == 1011000001, str(r))

# 4. 详情 + 可见性
_, r = req("GET", f"/knowledge/kb/get?id={private_id}", token=admin)
check("admin 看私有库详情", r["code"] == 0, str(r))
fields = set(r["data"].keys()) if r["data"] else set()
check("契约字段齐全", fields == {"id", "name", "description", "isPrivate", "documentCount", "memberCount", "createdAt", "updatedAt"}, str(sorted(fields)))
_, r = req("GET", f"/knowledge/kb/get?id={private_id}", token=test)
check("非成员访问私有库 403", r["code"] == 1011000002, str(r))
_, r = req("GET", f"/knowledge/kb/get?id={shared_id}", token=test)
check("非成员访问共享库 200", r["code"] == 0, str(r))

# 5. 分页/列表可见性
_, r = req("GET", "/knowledge/kb/page?pageNo=1&pageSize=10", token=test)
ids = [x["id"] for x in r["data"]["list"]]
check("test 分页仅见共享库", private_id not in ids and shared_id in ids, str(ids))
_, r = req("GET", "/knowledge/kb/list", token=admin)
ids = [x["id"] for x in r["data"]]
check("admin 列表含两库", private_id in ids and shared_id in ids, str(ids))

# 6. 更新（EDITOR 无权限前）
_, r = req("PUT", "/knowledge/kb/update", {"id": private_id, "name": "验收测试-私有库", "description": "已更新", "isPrivate": True}, admin)
check("admin 更新私有库", r["code"] == 0, str(r))

# 7. 成员管理
_, r = req("POST", "/knowledge/kb-member/create", {"kbId": private_id, "userId": 104, "role": "EDITOR"}, admin)
check("添加成员 test(EDITOR)", r["code"] == 0, str(r))
_, r = req("POST", "/knowledge/kb-member/create", {"kbId": private_id, "userId": 104, "role": "EDITOR"}, admin)
check("重复添加成员拒绝", r["code"] == 1011001000, str(r))
_, r = req("POST", "/knowledge/kb-member/create", {"kbId": private_id, "userId": 1, "role": "VIEWER"}, admin)
check("添加所有者被拒", r["code"] == 1011001003, str(r))
_, r = req("GET", "/knowledge/kb/get?id=" + str(private_id), token=test)
check("成员可见私有库", r["code"] == 0 and r["data"]["memberCount"] == 1, str(r))
_, r = req("PUT", "/knowledge/kb/update", {"id": private_id, "name": "验收测试-私有库", "description": "EDITOR 尝试", "isPrivate": True}, test)
check("EDITOR 成员更新被拒", r["code"] == 1011000003, str(r))
_, r = req("POST", "/knowledge/kb-member/create", {"kbId": private_id, "userId": 107, "role": "VIEWER"}, test)
check("EDITOR 成员管理成员被拒", r["code"] == 1011000003, str(r))
_, r = req("GET", "/knowledge/kb-member/page?kbId=" + str(private_id), token=admin)
check("成员分页", r["code"] == 0 and len(r["data"]["list"]) == 1, str(r))

# 8. 删除成员 + 删除知识库
member_id = req("GET", "/knowledge/kb-member/page?kbId=" + str(private_id), token=admin)[1]["data"]["list"][0]["id"]
_, r = req("DELETE", f"/knowledge/kb-member/delete?id={member_id}", token=admin)
check("删除成员", r["code"] == 0, str(r))
_, r = req("DELETE", f"/knowledge/kb/delete?id={shared_id}", token=admin)
check("删除共享库", r["code"] == 0, str(r))
_, r = req("GET", f"/knowledge/kb/get?id={shared_id}", token=admin)
check("删除后查询不存在", r["code"] == 1011000000, str(r))

# 9. 落库验证
print("\n===== 结果汇总 =====")
passed = sum(1 for _, ok, _ in results if ok)
print(f"通过 {passed}/{len(results)}")
for name, ok, detail in results:
    if not ok:
        print(f"  FAIL: {name} -> {detail}")
