"""Registry of runnable systems: name -> SystemSpec."""

from tracemem.components import GoldExtractor, GoldMatcher, GoldResolver, GoldRetriever, RuleAnswerer
from tracemem.pipeline import TraceMemPipeline
from tracemem.systems.base import MemorySystem, SystemSpec
from tracemem.systems.probes import (
    AlwaysConflictProbe,
    AlwaysNoneProbe,
    AlwaysOldestProbe,
    LatestCandidateProbe,
    LatestMentionProbe,
    OracleProbe,
)



def _gold_pipeline(meta, gold):
    """TraceMem's pipeline with every component replaced by its gold stand-in."""
    return TraceMemPipeline(meta, GoldExtractor(gold), GoldMatcher(), GoldResolver(gold), GoldRetriever(gold),
                            RuleAnswerer(), name="pipeline-gold")


REGISTRY: dict[str, SystemSpec] = {
    spec.name: spec
    for spec in [
        SystemSpec("oracle", OracleProbe, True, "probe: replays the gold answer; must score perfectly"),
        SystemSpec("always-oldest", AlwaysOldestProbe, True, "probe: first value ever stated; stale exactly where that value was replaced and not later restored"),
        SystemSpec("latest-candidate", LatestCandidateProbe, True, "probe: newest value from any statement that becomes a memory record"),
        SystemSpec("latest-mention", LatestMentionProbe, True, "probe: newest value mentioned in any way"),
        SystemSpec("always-conflict", AlwaysConflictProbe, True, "probe: always reports a conflict (refusal bound)"),
        SystemSpec("pipeline-gold", _gold_pipeline, True, "mock: TraceMem's pipeline wired from gold stand-ins"),
        SystemSpec("always-none", AlwaysNoneProbe, True, "probe: always says nothing is settled (refusal bound)"),
    ]
}

__all__ = ["REGISTRY", "MemorySystem", "SystemSpec"]
