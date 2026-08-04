"""Relationship-graph queries — Phase 1 T5 (session `1b`).

networkx in memory (ARCHITECTURE: a few thousand nodes — a graph database is an
operational dependency for no gain). Nodes are spell ids; an edge whose target
never resolved to an id gets a `("name", target_name)` pseudo-node so the
connection is still traversable and visibly unresolved.

## Build-dependent expansion

`amplifies_school` edges target a *school*, not a spell. Passing `build_spec`
(an iterable of the build's spell ids) expands each such edge into concrete
`amplifies` edges to every build ability of that school — including hybrid
double-dipping (primer §1: Shadowflame receives Shadow AND Fire modifiers), so
an "increases Fire damage" amplifier reaches a Shadowflame ability. Expanded
edges are tagged `expanded_from_school` and keep the school edge's (lower)
confidence: they are predictions until proc-tested (primer §5).
"""
import json

import networkx as nx

from .mechanics import HYBRID_SCHOOLS, SCHOOL_BITS

# school name -> set of component pure schools (hybrids double-dip, primer §1)
_COMPONENTS = {name: {name} for name in SCHOOL_BITS.values()}
for mask, name in HYBRID_SCHOOLS.items():
    _COMPONENTS[name] = {pure for bit, pure in SCHOOL_BITS.items() if mask & bit}


def school_components(school):
    """The pure schools a school name receives modifiers from."""
    if school is None:
        return set()
    if school in _COMPONENTS:
        return _COMPONENTS[school]
    return set(school.split("+"))  # unnamed multi-school masks render as A+B


def _build_schools(conn, build_spec):
    """{spell_id: school} for a build's abilities, from spell_mechanics."""
    schools = {}
    ids = list(build_spec)
    if not ids:
        return schools
    marks = ",".join("?" * len(ids))
    for spell_id, school in conn.execute(
            f"SELECT spell_id, school FROM spell_mechanics "
            f"WHERE spell_id IN ({marks})", ids):
        if school:
            schools[spell_id] = school
    return schools


def build_graph(conn, build_spec=None):
    """The full relationship graph as a `networkx.MultiDiGraph`.

    Every stored edge appears with its full attribute set. With `build_spec`,
    `amplifies_school` edges additionally expand into concrete `amplifies`
    edges against the build's same-school abilities (see module docstring).
    """
    g = nx.MultiDiGraph()
    rows = conn.execute(
        """SELECT source_spell_id, target_spell_id, target_name, relation_type,
                  magnitude, magnitude_unit, condition_json, direction,
                  source_tier, evidence_ref, confidence
           FROM spell_relationships""").fetchall()

    build_schools = _build_schools(conn, build_spec) if build_spec else {}

    for (src, dst, dst_name, relation, magnitude, unit, condition_json,
         direction, tier, evidence, confidence) in rows:
        condition = json.loads(condition_json) if condition_json else {}
        target = dst if dst is not None else ("name", dst_name)
        g.add_edge(src, target, relation_type=relation, magnitude=magnitude,
                   magnitude_unit=unit, condition=condition,
                   direction=direction, source_tier=tier,
                   evidence_ref=evidence, confidence=confidence)

        if relation == "amplifies_school" and build_schools:
            school = condition.get("school")
            for spell_id, spell_school in build_schools.items():
                if spell_id == src:
                    continue
                if school in school_components(spell_school):
                    g.add_edge(src, spell_id, relation_type="amplifies",
                               magnitude=magnitude, magnitude_unit=unit,
                               condition={**condition,
                                          "expanded_from_school": school},
                               direction="source_affects_target",
                               source_tier=tier, evidence_ref=evidence,
                               # a school-expanded edge is a PREDICTION
                               confidence="inferred")
    return g


def neighbourhood(conn, spell_id, depth=2, build_spec=None):
    """Everything within `depth` hops of a spell, both directions.

    Returns `{"nodes": [...], "edges": [edge dicts]}` — a serialisable slice,
    not a graph object, so the CLI/API layers can render it directly.
    """
    g = build_graph(conn, build_spec)
    if spell_id not in g:
        return {"nodes": [], "edges": []}
    sub = nx.ego_graph(g.to_undirected(as_view=False), spell_id, radius=depth)
    edges = []
    for src, dst, data in g.edges(data=True):
        if src in sub and dst in sub:
            edges.append({"source": src, "target": dst, **data})
    return {"nodes": sorted(sub.nodes, key=str), "edges": edges}


def find_clusters(conn, min_size=3, build_spec=None):
    """Densely-interconnected subgraphs — lego candidates (Phase 4).

    Current implementation: connected components of the undirected projection
    (trigger edges excluded — the trigger web strings most of the DBC together
    and would merge everything into one giant component), size-filtered, sorted
    by internal edge density. Deliberately simple; Phase 4 refines it.
    """
    g = build_graph(conn, build_spec)
    filtered = nx.MultiDiGraph()
    filtered.add_nodes_from(g.nodes)
    for src, dst, data in g.edges(data=True):
        if data["relation_type"] != "triggers":
            filtered.add_edge(src, dst, **data)
    undirected = filtered.to_undirected(as_view=False)
    undirected.remove_nodes_from(list(nx.isolates(undirected)))

    clusters = []
    for component in nx.connected_components(undirected):
        if len(component) < min_size:
            continue
        sub = undirected.subgraph(component)
        n = len(component)
        density = sub.number_of_edges() / (n * (n - 1) / 2) if n > 1 else 0
        clusters.append({"nodes": sorted(component, key=str), "size": n,
                         "edges": sub.number_of_edges(), "density": density})
    return sorted(clusters, key=lambda c: -c["density"])


def path_between(conn, spell_a, spell_b, build_spec=None):
    """How two spells connect, if at all: the shortest undirected path, with
    each hop's edge details. Returns None when no connection exists."""
    g = build_graph(conn, build_spec)
    if spell_a not in g or spell_b not in g:
        return None
    undirected = g.to_undirected(as_view=False)
    try:
        nodes = nx.shortest_path(undirected, spell_a, spell_b)
    except nx.NetworkXNoPath:
        return None
    hops = []
    for a, b in zip(nodes, nodes[1:]):
        data = (g.get_edge_data(a, b) or g.get_edge_data(b, a) or {})
        first = next(iter(data.values()), {})
        hops.append({"from": a, "to": b,
                     "relation_type": first.get("relation_type"),
                     "evidence_ref": first.get("evidence_ref")})
    return {"nodes": nodes, "hops": hops}


def gating_requirements(conn, cluster_nodes, build_spec=None):
    """Union of all `condition_json` across a cluster's edges — what you must
    own/satisfy for the cluster to work. This is what turns the graph into
    build advice."""
    g = build_graph(conn, build_spec)
    node_set = set(cluster_nodes)
    requirements = []
    seen = set()
    for src, dst, data in g.edges(data=True):
        if src in node_set and dst in node_set and data.get("condition"):
            key = json.dumps(data["condition"], sort_keys=True)
            if key not in seen:
                seen.add(key)
                requirements.append({"condition": data["condition"],
                                     "relation_type": data["relation_type"],
                                     "between": [src, dst]})
    return requirements
