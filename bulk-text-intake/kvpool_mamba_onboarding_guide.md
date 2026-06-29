# KVPool Mamba Cache 入门与源码阅读指南

## 1. 目标

这份指南适合准备承接 KVPool 中 Mamba cache 工作、但暂时没有 vLLM、KV cache 或 Mamba 基础的开发者。

第一阶段不要求理解 Mamba 的完整数学原理，也不要求读完所有 kernel。建议先达到下面的目标：

> 能完整解释一个 hybrid Attention/Mamba 请求，如何完成 Mamba block 分配、KVPool 保存、前缀命中、状态加载和最终释放。

不建议一开始逐行阅读 `pool_worker.py`。这个文件同时包含 Attention、MLA、Mamba、压缩 cache、layerwise 传输和多个存储后端，很容易失去主线。

## 2. 最小心智模型

开始阅读前，先记住以下区别。

### 2.1 Attention KV cache

Attention 为历史 token 保存 K/V：

```text
token 0-15   -> KV block 10
token 16-31  -> KV block 11
token 32-47  -> KV block 12
```

这些 block 可以连续保存和加载。一个前缀命中通常要求从开头开始连续命中。

### 2.2 Mamba cache

Mamba 保存递归状态。某个位置的状态可以理解为：

```text
读取完此前全部 token 后，模型内部状态的快照
```

Mamba 继续计算时主要需要最新状态，而不是此前所有状态。

### 2.3 align 模式

`mamba_cache_mode="align"` 只在合法 block 边界保留状态快照。没有真实状态的位置使用 null block 占位：

```text
token:       0 .... 15 | 16 .... 31 | 32 .... 47 | 48 .... 63
Attention:   block 10    block 11     block 12     block 13
Mamba:       null        null         null         state block 23
```

需要牢牢记住：

```text
block_id=0 通常表示 null block，不是有效 Mamba 状态。
```

## 3. 推荐阅读路线

建议分五个阶段阅读，每个阶段只解决一组问题。

## 4. 第一阶段：上游 vLLM cache 基础

这一阶段的目标是理解 KVPool 接收到的数据结构从哪里来。

### 4.1 阅读 MambaSpec

文件：

`vllm/vllm/v1/kv_cache_interface.py`

入口：

```python
class MambaSpec(KVCacheSpec)
```

重点字段：

| 字段 | 需要理解的问题 |
| --- | --- |
| `shapes` | 一个 Mamba layer 包含多少个状态张量？ |
| `dtypes` | 不同状态张量是否允许使用不同类型？ |
| `block_size` | 状态快照对应多少 token？ |
| `mamba_cache_mode` | `none`、`all`、`align` 有什么区别？ |
| `num_speculative_blocks` | 推测解码为什么需要额外状态块？ |
| `page_size_bytes` | 一个 Mamba 状态页占多少内存？ |

读完后应该能回答：

```text
一个 Mamba cache block 在内存中包含什么？
```

### 4.2 阅读 BlockPool 和 null block

文件：

`vllm/vllm/v1/core/block_pool.py`

重点查看 `BlockPool.__init__()` 中 null block 的创建：

```python
self.null_block = self.free_block_queue.popleft()
self.null_block.is_null = True
```

需要理解：

- null block 为什么固定占用一个物理 block id？
- 为什么 null block 的引用计数不能按普通 block 处理？
- 为什么保存、加载和释放时必须跳过它？

### 4.3 阅读 MambaManager

文件：

`vllm/vllm/v1/core/single_type_kv_cache_manager.py`

入口：

```python
class MambaManager(SingleTypeKVCacheManager)
```

第一遍只看以下函数：

1. `find_longest_cache_hit`
2. `remove_skipped_blocks`
3. `get_num_blocks_to_allocate`
4. `allocate_new_blocks`
5. `cache_blocks`

阅读时回答：

- 为什么 Mamba 只保留最近状态？
- 为什么 align 模式会在 block table 中填入 null block？
- 为什么 Mamba cache hit 从右向左查找？
- 当前状态何时复制到新 block？
- 旧状态在什么条件下释放？
- 推测解码状态块如何复用？

这一阶段不需要阅读 Mamba CUDA、Triton 或 NPU kernel。

## 5. 第二阶段：KVPool Scheduler

文件：

`vllm-ascend/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_scheduler.py`

Scheduler 不直接搬运数据。它负责回答：

```text
外部缓存命中了多少 token？
需要为哪些 token 分配本地 block？
哪些 block 正在异步发送，暂时不能释放？
```

### 5.1 推荐阅读顺序

1. `KVPoolScheduler.__init__`
2. `_uses_hybrid_kv_cache`
3. `_infer_mamba_groups`
4. `_infer_group_block_sizes`
5. `_infer_cache_transfer_granularity`
6. `get_num_new_matched_tokens`
7. `update_state_after_alloc`
8. `build_connector_meta`
9. `touch_sending_mamba_blocks`
10. `update_connector_output`
11. `request_finished_all_groups`

### 5.2 重点理解的状态

| 状态 | 作用 |
| --- | --- |
| `use_hybrid` | 是否使用多个异构 cache group |
| `mamba_group_ids` | 哪些 group 保存 Mamba 状态 |
| `grouped_block_size` | 各 group 考虑 PCP/DCP 后的 block size |
| `cache_transfer_granularity` | 所有 group 共同允许的传输边界 |
| `load_specs` | 每个请求需要从 KVPool 加载多少 token |
| `sending_blocks` | 每个发送事件正在保护哪些 Mamba block |
| `sending_events` | 每个事件已经收到多少 Worker 完成报告 |

### 5.3 Mamba block 生命周期主线

```text
build_connector_meta
  -> touch_sending_mamba_blocks
  -> BlockPool.touch 增加引用
  -> Worker 异步发送
  -> Worker metadata 回传 event_id
  -> update_connector_output
  -> 所有 Worker 完成后 free_blocks
```

读完后应该能解释：

```text
为什么请求已经结束，某些 Mamba block 仍然不能立即释放？
```

## 6. 第三阶段：KVPool Worker

文件：

`vllm-ascend/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/pool_worker.py`

Worker 负责注册缓存内存、生成传输任务并与后端交互。

### 6.1 推荐阅读顺序

1. `_init_kv_transfer_config`
2. `_infer_group_uses_align_state`
3. `_infer_cache_group_metadata`
4. `register_kv_caches`
5. `_start_kv_transfer_threads`
6. `lookup`
7. `lookup_scheduler`
8. `start_load_kv`
9. `wait_for_save`
10. `build_connector_worker_meta`

### 6.2 阅读 register_kv_caches 时关注

每个 Mamba layer 可能包含多个状态张量。Worker 会记录：

- 状态张量基础地址。
- 单 block 字节数。
- block stride。
- 所属 layer。
- 所属 cache group。
- backend 需要注册的完整内存区域。

需要回答：

```text
给定 group_id、layer_name 和 block_id，代码如何计算实际设备地址？
```

### 6.3 阅读 lookup 时关注

普通 Attention 使用连续命中规则。

Mamba align group 使用逆序查找：

```python
for index in range(len(ends) - 1, -1, -1):
    if exists[index] and aligned:
        hit_end = ends[index]
        break
```

需要回答：

- 为什么不能遇到第一个 miss 就停止？
- 为什么命中位置必须满足共同传输粒度？
- 为什么 Mamba align group 不作为整个请求的严格 lookup gate？

## 7. 第四阶段：真正的数据传输

文件：

`vllm-ascend/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/kv_transfer.py`

重点类：

```python
class KVCacheStoreSendingThread
class KVCacheStoreRecvingThread
```

### 7.1 保存路径

重点阅读：

```python
KVCacheStoreSendingThread._handle_request
```

跟踪以下流程：

```text
遍历 cache group
  -> 取出 block_ids_by_group[group_id]
  -> 按 group block size 生成 hash
  -> 跳过 block_id <= 0
  -> 生成外部 key
  -> 查询 key 是否已经存在
  -> 计算每个状态张量的地址和长度
  -> 等待 NPU event
  -> backend.put
  -> 在 finally 中上报 event_id 完成
```

### 7.2 null block 过滤

文件：

`vllm-ascend/vllm_ascend/distributed/kv_transfer/kv_pool/ascend_store/config_data.py`

重点函数：

```python
ChunkedTokenDatabase.process_tokens_with_block_ids
```

核心逻辑：

```python
if skip_null_blocks and block_id <= 0:
    continue
```

需要确认 null block 不会：

- 生成外部 key。
- 生成传输地址。
- 调用 backend。
- 进入普通物理 block 释放流程。

### 7.3 完成事件

发送线程使用 `finally` 上报完成：

```python
finally:
    self.mark_completed_events(req_meta.event_id)
```

这一点很重要，因为以下情况也必须解除 Scheduler 的 block 引用：

- 外部 key 已经存在，不需要发送。
- 请求没有有效 Mamba block。
- backend 抛出异常。

## 8. 第五阶段：手工跟踪一个请求

不要只看函数。构造一个简单示例，并逐步记录字段变化。

### 8.1 示例参数

| 字段 | 示例值 |
| --- | --- |
| Attention group id | `0` |
| Mamba group id | `1` |
| Attention block size | `16` |
| Mamba block size | `64` |
| Attention block ids | `[10, 11, 12, 13]` |
| Mamba block ids | `[0, 0, 0, 23]` |
| hash block size | `16` |
| transfer granularity | `64` |

### 8.2 跟踪链路

```text
SchedulerOutput
  -> RequestTracker
  -> ReqMeta.block_ids_by_group
  -> KVPoolWorker.start_load_kv / wait_for_save
  -> KVCacheStoreSendingThread._handle_request
  -> backend.put/get
  -> worker completed_events
  -> KVPoolScheduler.update_connector_output
```

### 8.3 每一步记录模板

```markdown
## 当前函数

- request_id:
- token_len:
- group_id:
- group block_size:
- block_ids:
- block_hashes:
- generated keys:
- data addresses:
- event_id:
- block ref count before:
- block ref count after:
```

建议至少完整跟踪：

1. 第一次请求，外部完全 miss。
2. 第一次请求计算完成并保存。
3. 第二次相同请求命中 Attention 和 Mamba 状态。
4. 请求结束但 Mamba 状态仍在发送。
5. 所有 Worker 完成后释放状态块。

## 9. 测试阅读顺序

### 9.1 上游 vLLM 测试

1. `vllm/tests/v1/e2e/general/test_mamba_prefix_cache.py`
2. `vllm/tests/v1/core/test_prefix_caching.py`
3. `vllm/tests/v1/worker/test_mamba_utils.py`
4. `vllm/tests/v1/attention/test_mamba_update_block_table.py`

重点寻找：

- null block 分布。
- block table 的变化。
- align 边界。
- prefix hit 后状态恢复。
- speculative decode 下的状态拷贝。

### 9.2 KVPool 测试

1. `vllm-ascend/tests/ut/distributed/ascend_store/test_pool_worker.py`
2. `vllm-ascend/tests/ut/distributed/ascend_store/test_pool_scheduler.py`

当前测试主要覆盖：

- Mamba group 检测。
- completed event metadata。
- hybrid 请求的延迟释放。

## 10. 推荐的第一个练习

承接代码前，可以先补充几组纯单元测试：

1. `MambaSpec` group 能被正确识别。
2. 非 `align` 模式被拒绝。
3. 保存时跳过 `block_id=0`。
4. 加载时跳过 `block_id=0`。
5. lookup 从右向左寻找最新状态。
6. 未完成发送事件不会释放 block。
7. 多 Worker 全部完成后才释放 block。
8. backend 异常时完成事件仍被报告。

这些测试不要求真实 NPU，可以使用 mock backend、mock block pool 和构造的 `ReqMeta`。

## 11. 必须守住的五个不变量

以后修改代码时，优先检查这些不变量有没有被破坏。

### 11.1 null block 不参与真实传输

```text
block_id=0 不能被当成有效 Mamba 状态保存或加载。
```

### 11.2 Mamba 命中必须位于合法边界

```text
hit_tokens % cache_transfer_granularity == 0
```

### 11.3 Attention 和 Mamba key 必须隔离

外部 key 必须包含 `kv_cache_group_id`，并使用正确的 TP rank 规则。

### 11.4 所有 group 对应同一个前缀

不能恢复 128 token 的 Attention KV，却只恢复 64 token 对应的 Mamba state。

### 11.5 异步发送完成前不能复用物理 block

```text
touch block
  -> 所有 Worker 完成
  -> free block
```

顺序不能被打乱。

## 12. 建议暂时跳过的内容

刚开始可以暂时不读：

- Mamba CUDA/Triton/NPU kernel 的数学细节。
- layerwise KVPool 实现。
- MLA 和 DeepSeek 压缩 cache family。
- Memcache GVA 传输优化。
- PCP/DCP 的复杂地址布局。
- 推测解码的全部状态修正逻辑。

先把 `TP=1、PP=1、PCP=1、DCP=1、非 layerwise、align 模式` 的主流程读通，再逐步增加变量。

## 13. 第一周建议计划

### 第 1 天

- 阅读 `MambaSpec`、`BlockPool`。
- 理解 block、page、group、null block。
- 画出 Attention 与 Mamba block table 示例。

### 第 2 天

- 阅读 `MambaManager` 的五个关键函数。
- 跟踪一次 align 模式分配和旧状态释放。

### 第 3 天

- 阅读 `KVPoolScheduler`。
- 画出 `RequestTracker -> ReqMeta` 的字段变化。

### 第 4 天

- 阅读 `KVPoolWorker.register_kv_caches` 和 lookup。
- 手工计算一次 Mamba block 地址。

### 第 5 天

- 阅读发送线程。
- 跟踪 `touch -> put -> completed event -> free`。

### 第 6 天

- 阅读上游和 KVPool 测试。
- 运行不依赖真实 NPU 的相关单元测试。

### 第 7 天

- 补充一个 null block 或完成事件相关单元测试。
- 用自己的语言讲一遍完整请求生命周期。

## 14. 判断是否已经入门

能够回答以下问题，就可以开始承接小范围修改：

1. `MambaSpec.shapes` 为什么是多个 shape？
2. `block_id=0` 在 Mamba align 模式中表示什么？
3. 为什么 Mamba lookup 从右向左，而 Attention 从左向右？
4. 为什么 Mamba group 使用完整 TP rank 生成 key？
5. 为什么不同 cache group 要计算最小公倍数传输粒度？
6. 为什么保存前要 `touch` Mamba block？
7. `event_id` 如何跨 Worker 聚合？
8. backend 异常时为什么仍要报告完成？
9. 请求结束和物理 block 真正释放为什么不是同一时刻？
10. 哪些路径明确不支持 Mamba prefix caching？

## 15. 相关文档

更完整的源码解读见：

[`kvpool_mamba_code_analysis.md`](kvpool_mamba_code_analysis.md)

建议将该文档作为源码索引，将本指南作为实际阅读和学习顺序。
