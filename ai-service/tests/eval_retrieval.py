# -*- coding: utf-8 -*-
"""P1-1: 检索评测集 — 20 queries, ground truth = doc ids that SHOULD be retrieved.
Metrics: Recall@5, MRR@5, avg latency; modes: dense/bm25/hybrid.
"""
import json, time, urllib.request

BASE = 'http://localhost:8000'

DATASET = [
    # semantic
    ('新人入职第一天应该做什么准备', ['9011']),
    ('团队怎么保证代码合并的质量', ['9012']),
    ('这段时间团队做了哪些东西', ['9015']),
    ('系统里各个数据分别存在什么地方', ['9013']),
    ('上传的文档半天没出现在知识库里怎么办', ['9014']),
    ('服务之间怎么传递消息的', ['9013']),
    ('前端页面显示的都是乱码如何解决', ['9014']),
    ('项目接下来有什么打算和计划', ['9015']),
    # keyword exact
    ('Knife4j 接口文档地址是什么', ['9011']),
    ('Redis 连不上怎么排查', ['9014']),
    ('数据库建表用什么字符集', ['9014']),
    ('doc-pipeline 是用来干什么的', ['9013']),
    ('登录默认账号密码是什么', ['9011']),
    # analytical / cross-doc
    ('为什么不用 RabbitMQ 而用 Redis Streams', ['9013']),
    ('扫描版 PDF 能不能处理', ['9015']),
    ('消费者吞吐量上不去的原因可能是什么', ['9015']),
    ('OCR 能力规划在哪个季度落地', ['9015']),
    ('tenant-id 请求头是干什么的', ['9011', '9013']),
    # hard negatives
    ('今天天气怎么样', []),
    ('怎么写一篇网络小说', []),
]

KNOWN = {'9011', '9012', '9013', '9014', '9015'}

def search(query, mode, top_k=5):
    body = json.dumps({'query': query, 'kbId': '1', 'mode': mode, 'topK': top_k}).encode('utf-8')
    req = urllib.request.Request(BASE + '/ai/search', data=body,
                                 headers={'Content-Type': 'application/json'}, method='POST')
    t0 = time.perf_counter()
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))
    ms = int((time.perf_counter() - t0) * 1000)
    return [h['documentId'] for h in r['results']], ms

def evaluate(mode):
    recall_hits, rr_sum, lats, noise_fired = 0, 0.0, [], 0
    detail = []
    for q, gold in DATASET:
        ids, ms = search(q, mode)
        lats.append(ms)
        if not gold:
            if ids and str(ids[0]) in KNOWN:
                noise_fired += 1
            detail.append((q, 'NEG', ids[:2], ms))
            continue
        hit_positions = [i + 1 for i, d in enumerate(ids) if str(d) in gold]
        if hit_positions:
            recall_hits += 1
            rr_sum += 1.0 / hit_positions[0]
        detail.append((q, 'OK' if hit_positions else 'MISS', hit_positions or ids[:2], ms))
    n_gold = sum(1 for _, g in DATASET if g)
    return {
        'mode': mode,
        'recall5': recall_hits / n_gold,
        'mrr5': rr_sum / n_gold,
        'avg_ms': sum(lats) / len(lats),
        'noise': '%d/%d' % (noise_fired, len(DATASET) - n_gold),
        'detail': detail,
    }

results = {}
for mode in ('dense', 'bm25', 'hybrid'):
    print('\n===== MODE: %s =====' % mode)
    r = evaluate(mode)
    results[mode] = r
    print('Recall@5=%.0f%%  MRR@5=%.3f  avg=%dms  noise_fired=%s' % (
        r['recall5'] * 100, r['mrr5'], r['avg_ms'], r['noise']))
    for q, tag, pos, ms in r['detail']:
        print('  [%s] %s -> %s (%dms)' % (tag, q, pos, ms))

with open(r'D:\神之龙仓\.openclaw\tmp\eval_results.json', 'w', encoding='utf-8') as f:
    json.dump({k: {kk: vv for kk, vv in v.items() if kk != 'detail'} for k, v in results.items()},
              f, ensure_ascii=False, indent=2)

print('\n===== SUMMARY =====')
print('%-8s %9s %9s %9s %12s' % ('mode', 'Recall@5', 'MRR@5', 'avg_ms', 'noise_fired'))
for m, r in results.items():
    print('%-8s %8.0f%% %9.3f %8dms %12s' % (m, r['recall5'] * 100, r['mrr5'], r['avg_ms'], r['noise']))
