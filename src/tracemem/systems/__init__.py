"""Registry of runnable systems: name -> SystemSpec."""

from tracemem.components import GoldExtractor, GoldMatcher, GoldResolver, GoldRetriever, RuleAnswerer
from tracemem.pipeline import TraceMemPipeline
from tracemem.resolver import LLMResolver
from tracemem.systems.base import MemorySystem, SystemSpec
from tracemem.systems.comparison import NAMES as COMPARISON_SYSTEMS, factory as comparison_factory
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


def _resolver_dev_pipeline(meta, gold):
    """A real resolver with gold upstream/retrieval; a module diagnostic, not a baseline."""
    if gold is None:
        raise ValueError("pipeline-resolver-dev requires gold stand-ins")
    # Configuration and SDK construction happen only when this system is run.
    resolver = LLMResolver.from_env()
    return TraceMemPipeline(meta, GoldExtractor(gold), GoldMatcher(), resolver, GoldRetriever(gold),
                            RuleAnswerer(), name="pipeline-resolver-dev")


REGISTRY: dict[str, SystemSpec] = {
    spec.name: spec
    for spec in [
        SystemSpec("oracle", OracleProbe, True, "probe: replays the gold answer; must score perfectly"),
        SystemSpec("always-oldest", AlwaysOldestProbe, True, "probe: first value ever stated; stale exactly where that value was replaced and not later restored"),
        SystemSpec("latest-candidate", LatestCandidateProbe, True, "probe: newest value from any statement that becomes a memory record"),
        SystemSpec("latest-mention", LatestMentionProbe, True, "probe: newest value mentioned in any way"),
        SystemSpec("always-conflict", AlwaysConflictProbe, True, "probe: always reports a conflict (refusal bound)"),
        SystemSpec("pipeline-gold", _gold_pipeline, True, "mock: TraceMem's pipeline wired from gold stand-ins"),
        SystemSpec("pipeline-resolver-dev", _resolver_dev_pipeline, True,
                   "mock: real resolver with gold extraction, matching and retrieval; development diagnostic"),
        SystemSpec("always-none", AlwaysNoneProbe, True, "probe: always says nothing is settled (refusal bound)"),
        *[SystemSpec(name, comparison_factory(name), False,
                     "controlled baseline/ablation: shared gold candidates and model; requires gold_candidates")
          for name in COMPARISON_SYSTEMS],
    ]
}

__all__ = ["REGISTRY", "MemorySystem", "SystemSpec"]
