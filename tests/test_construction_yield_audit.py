from scripts.construction_yield_audit import cluster_interval, source_id


def test_recovers_base_sources_across_frozen_families() -> None:
    assert source_id({
        "case_id": "uan:a-s2-disjoint:v2:hotpotqa:abc:order2",
        "family": "a-s2-disjoint:order2",
    }) == "hotpotqa:abc"
    assert source_id({
        "case_id": "uan-news:n-s2-v0:v2:nq:test7",
        "family": "news:n-s2-v0",
    }) == "nq:test7"
    assert source_id({
        "case_id": "holdout-v1:n-s2-v0:msmarco:42",
        "family": "holdout-v1:n-s2-v0",
    }) == "msmarco:42"


def test_cluster_interval_does_not_treat_candidates_as_independent() -> None:
    rows = []
    for source, value in (("d:s1", True), ("d:s2", False)):
        rows.extend({"source_id": source, "hit": value} for _ in range(8))
    interval = cluster_interval(rows, lambda row: row["hit"], "test", draws=1000)
    assert interval == [0.0, 1.0]
