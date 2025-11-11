# Kafka Throughput Optimization Playbook

This guide outlines a repeatable approach for benchmarking and tuning the Kafka-based messaging layer that powers the NINA Guardrail Monitor.  Follow the sections in order; capture metrics after each change so you can prove the improvement (or roll it back quickly if latency regresses).

---

## 1. Establish a Baseline

1. **Inventory Current Topics**
   - Topic names, partitions, replication factor.
   - Message schema & typical payload size.
   - Producers/consumers and their client libraries.
2. **Capture Current Metrics**
   - Throughput (msg/s, MB/s) per topic.
   - End-to-end latency (producer send → consumer commit).
   - Lag per consumer group.
   - Producer error rate (`retries`, `timeouts`).
   - Broker resource usage (CPU, disk, network).
3. **Traffic Simulation**
   - Reproduce typical and peak load using a load generator (e.g. `kafkacat`, `kafka-producer-perf-test.sh`, or a custom script).
   - Record baseline numbers in a shared sheet/doc.

---

## 2. Producer Tuning Checklist

| Knob | Default | Suggested Starting Point | Notes |
|------|---------|--------------------------|-------|
| `acks` | `1` | `all` (if consistency > latency) | Guarantees replication but increases latency; consider idempotent producer. |
| `enable.idempotence` | `false` | `true` | Prevents duplicates when retries happen. |
| `compression.type` | `none` | `lz4` or `zstd` | Compression reduces bandwidth; measure CPU trade-off. |
| `linger.ms` | `0` | `5-20` | Adds batching window; higher values improve throughput but add latency. |
| `batch.size` | `16384` bytes | `64KB-128KB` | Keep under broker `max.message.bytes`. |
| `max.in.flight.requests.per.connection` | `5` | `1` with idempotence, else 5 | Lower value ensures ordering when retries occur. |
| `retries` | `2147483647` | leave default | Combine with `delivery.timeout.ms`. |
| `delivery.timeout.ms` | `120000` | align with SLA | Maximum time before failing a send. |

**Workflow**
1. Enable compression → observe throughput & CPU.
2. Increase `batch.size` and `linger.ms` together while monitoring latency.
3. Enforce `acks=all` + `enable.idempotence` if message loss is unacceptable.
4. Document the final producer config per service.

---

## 3. Consumer Tuning Checklist

| Knob | Description | Suggested Range |
|------|-------------|-----------------|
| `fetch.min.bytes` / `fetch.max.wait.ms` | Controls batch retrieval size/wait | Start with `1MB / 50ms` for analytics consumers. |
| `max.partition.fetch.bytes` | Max bytes per partition per request | Increase if payloads are large (e.g. 5MB). |
| `max.poll.records` | Number of records returned per poll | Balance processing cost vs. commit frequency; try 500–1000. |
| `max.poll.interval.ms` | Max time between `poll()` calls | Ensure it exceeds worst-case processing time. |
| `session.timeout.ms` | Consumer heartbeat timeout | Align with broker/rebalance expectations. |
| `enable.auto.commit` | Automatic offset commits | Prefer manual commit after processing. |

**Parallelism**
- Ensure `# partitions >= # consumer instances`.
- For CPU-heavy processing, consider multi-threaded consumers or distributing across instances.

---

## 4. Broker & Cluster Considerations

1. **Partitions & Replication**
   - Increase partitions to scale consumers horizontally.
   - Keep replication factor ≥ 3 in production.
2. **Broker Resources**
   - Monitor disk throughput, network latency, page cache hits.
   - Ensure log segment sizes and retention align with throughput.
3. **Connection Pooling**
   - Use shared producer/consumer instances rather than recreating per request.
4. **Compression Support**
   - Ensure brokers support chosen compression (modern Kafka supports `gzip`, `snappy`, `lz4`, `zstd`).

---

## 5. Observability & Alerting

- **Metrics to gather**
  - Producer: `request-latency-avg`, `batch-size-avg`, `record-error-rate`.
  - Consumer: `records-lag-max`, `fetch-rate`, `poll-latency-avg`.
  - Broker JMX: `BytesInPerSec`, `BytesOutPerSec`, `UnderReplicatedPartitions`.
- **Tools**
  - Prometheus JMX exporter or Confluent Control Center.
  - Grafana dashboards for visibility.
  - Alert thresholds: lag > X messages, under-replicated partitions > 0, broker CPU > 80%.

---

## 6. Optimization Runbook

1. **Plan**
   - Select a single change (e.g., enable `lz4` compression).
   - Define hypothesis (expected throughput gain, acceptable latency budget).
2. **Apply**
   - Adjust configs via environment variables or config files.
   - Deploy to staging first; generate throughput similar to production.
3. **Measure**
   - Capture metrics pre- and post-change.
   - Compare latency, throughput, error rates.
4. **Decide**
   - Keep if metrics improve or stay within budget.
   - Roll back and log outcome if regression occurs.
5. **Document**
   - Update configuration management and this guide with lessons learned.

---

## 7. Suggested Improvement Sequence

1. **Enable Compression** (`lz4` or `zstd`) → measure bandwidth savings.
2. **Tune Producer Batching** (`batch.size`, `linger.ms`) for analytics-heavy topics.
3. **Optimize Consumer Throughput** (increase `max.poll.records`, check processing batch size).
4. **Partition Review** → ensure each topic has enough partitions for consumer parallelism.
5. **Introduce Parallel Consumers** for CPU-bound processing.
6. **Add Performance Monitoring Dashboard** to catch regressions early.
7. **Evaluate Read Replicas / Dedicated Analytics Brokers** if analytical workloads impact real-time ingest.

---

## 8. Deliverables Checklist

- [ ] Baseline report (metrics + current configs).
- [ ] Config change log with rationale and impact.
- [ ] Updated infrastructure-as-code / app configs.
- [ ] Grafana dashboard (or equivalent) monitoring producer/consumer/broker health.
- [ ] Runbook in the main repo referencing this playbook.

Once the baseline is captured, pick one knob at a time, follow the runbook, and record outcomes.  Small, measured steps keep the pipeline reliable while you squeeze out the throughput improvements.

