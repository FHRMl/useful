import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


class StaticGraphRepository:
    def __init__(self, json_path: str | Path):
        with Path(json_path).open("r", encoding="utf-8") as handle:
            self.data = json.load(handle)
        self._courses = {course["id"]: course for course in self.data["courses"]}
        self._knowledge = {point["id"]: point for point in self.data["knowledge_points"]}

    def list_courses(self) -> list[dict[str, Any]]:
        courses = []
        for course in self.data["courses"]:
            item = dict(course)
            item["kp_count"] = len(course.get("knowledge_ids", []))
            courses.append(item)
        return sorted(courses, key=lambda item: item["name"])

    def get_course(self, course_id: str) -> dict[str, Any] | None:
        course = self._courses.get(course_id)
        if not course:
            return None
        item = dict(course)
        item["knowledge_points"] = [
            self._knowledge[kp_id]
            for kp_id in course.get("knowledge_ids", [])
            if kp_id in self._knowledge
        ]
        item["clc"] = course.get("clc", {})
        item["dimensions"] = course.get("dimensions", [])
        return item

    def knowledge_name_map(self) -> dict[str, str]:
        return {point["id"]: point["name"] for point in self.data["knowledge_points"]}

    def course_name_map(self) -> dict[str, str]:
        return {course["id"]: course["name"] for course in self.data["courses"]}

    def graph(self, query: str = "") -> dict[str, Any]:
        nodes, links = self._build_graph()
        query = query.strip().lower()
        if not query:
            return {"nodes": nodes, "links": links}

        node_index = {node["id"]: node for node in nodes}
        matched = {
            node["id"]
            for node in nodes
            if query in node.get("name", "").lower()
            or query in node.get("category", "").lower()
            or query in str(node.get("code", "")).lower()
        }
        if not matched:
            return {"nodes": [], "links": []}

        expanded = set(matched)
        for link in links:
            if link["source"] in matched or link["target"] in matched:
                expanded.add(link["source"])
                expanded.add(link["target"])
        filtered_links = [
            link for link in links if link["source"] in expanded and link["target"] in expanded
        ]
        return {
            "nodes": [node_index[node_id] for node_id in expanded if node_id in node_index],
            "links": filtered_links,
        }

    def analysis(self) -> dict[str, Any]:
        nodes, links = self._build_graph()
        node_lookup = {node["id"]: node for node in nodes}
        degrees = Counter()
        for link in links:
            degrees[link["source"]] += 1
            degrees[link["target"]] += 1

        top_knowledge = []
        for point in self.data["knowledge_points"]:
            top_knowledge.append(
                {
                    "id": point["id"],
                    "name": point["name"],
                    "degree": degrees[point["id"]],
                    "source": point.get("source", ""),
                }
            )
        top_knowledge.sort(key=lambda item: (-item["degree"], item["name"]))

        shared_pairs = []
        courses = self.data["courses"]
        for left_index, left in enumerate(courses):
            left_set = set(left.get("knowledge_ids", []))
            for right in courses[left_index + 1 :]:
                shared = sorted(left_set.intersection(right.get("knowledge_ids", [])))
                if shared:
                    shared_pairs.append(
                        {
                            "left": left["name"],
                            "right": right["name"],
                            "count": len(shared),
                            "knowledge": [node_lookup[item]["name"] for item in shared],
                        }
                    )
        shared_pairs.sort(key=lambda item: (-item["count"], item["left"], item["right"]))

        dimension_counts = defaultdict(Counter)
        for course in courses:
            for dimension in course.get("dimensions", []):
                dimension_counts[dimension["dimension"]][dimension["value"]] += 1

        return {
            "top_knowledge": top_knowledge[:8],
            "shared_pairs": shared_pairs[:8],
            "dimension_counts": {
                key: [{"name": name, "count": count} for name, count in counter.most_common()]
                for key, counter in dimension_counts.items()
            },
            "node_count": len(nodes),
            "link_count": len(links),
        }

    def _build_graph(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        nodes: dict[str, dict[str, Any]] = {}
        links: list[dict[str, Any]] = []

        def add_node(node: dict[str, Any]) -> None:
            nodes[node["id"]] = node

        def add_link(source: str, target: str, relation: str) -> None:
            links.append({"source": source, "target": target, "relation": relation})

        for course in self.data["courses"]:
            add_node(
                {
                    "id": course["id"],
                    "name": course["name"],
                    "category": "课程",
                    "code": course.get("code", ""),
                    "symbolSize": 54,
                }
            )
            clc = course.get("clc", {})
            if clc:
                clc_id = f"CLC_{clc['code']}"
                add_node(
                    {
                        "id": clc_id,
                        "name": f"{clc['code']} {clc['name']}",
                        "category": "中图法",
                        "code": clc["code"],
                        "symbolSize": 34,
                    }
                )
                add_link(course["id"], clc_id, "中图法分类")
            for dimension in course.get("dimensions", []):
                dim_id = "DIM_{}_{}".format(dimension["dimension"], dimension["value"])
                add_node(
                    {
                        "id": dim_id,
                        "name": dimension["value"],
                        "category": dimension["dimension"],
                        "symbolSize": 32,
                    }
                )
                add_link(course["id"], dim_id, dimension["dimension"])
            for kp_id in course.get("knowledge_ids", []):
                add_link(course["id"], kp_id, "包含知识点")

        for point in self.data["knowledge_points"]:
            add_node(
                {
                    "id": point["id"],
                    "name": point["name"],
                    "category": "知识点",
                    "source": point.get("source", ""),
                    "symbolSize": 42,
                }
            )

        for relation in self.data.get("knowledge_relations", []):
            add_link(relation["source"], relation["target"], relation["relation"])

        return list(nodes.values()), links


class Neo4jGraphRepository:
    def __init__(self, uri: str, user: str, password: str):
        from neo4j import GraphDatabase

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()

    def list_courses(self) -> list[dict[str, Any]]:
        query = """
        MATCH (c:Course)
        OPTIONAL MATCH (c)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
        RETURN properties(c) AS course, count(kp) AS kp_count
        ORDER BY c.name
        """
        with self.driver.session() as session:
            rows = session.run(query)
            return [dict(row["course"], kp_count=row["kp_count"]) for row in rows]

    def get_course(self, course_id: str) -> dict[str, Any] | None:
        query = """
        MATCH (c:Course {id: $course_id})
        OPTIONAL MATCH (c)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)
        WITH c, collect(DISTINCT properties(kp)) AS knowledge_points
        OPTIONAL MATCH (c)-[:CLASSIFIED_BY]->(clc:CLCClass)
        WITH c, knowledge_points, collect(DISTINCT properties(clc)) AS clc_nodes
        OPTIONAL MATCH (c)-[:HAS_DIMENSION]->(d:DimensionValue)
        RETURN properties(c) AS course,
               knowledge_points,
               clc_nodes,
               collect(DISTINCT properties(d)) AS dimensions
        """
        with self.driver.session() as session:
            row = session.run(query, course_id=course_id).single()
        if not row:
            return None
        course = dict(row["course"])
        course["knowledge_points"] = [point for point in row["knowledge_points"] if point]
        course["clc"] = row["clc_nodes"][0] if row["clc_nodes"] else {}
        course["dimensions"] = [item for item in row["dimensions"] if item]
        return course

    def knowledge_name_map(self) -> dict[str, str]:
        with self.driver.session() as session:
            rows = session.run("MATCH (kp:KnowledgePoint) RETURN kp.id AS id, kp.name AS name")
            return {row["id"]: row["name"] for row in rows}

    def course_name_map(self) -> dict[str, str]:
        with self.driver.session() as session:
            rows = session.run("MATCH (c:Course) RETURN c.id AS id, c.name AS name")
            return {row["id"]: row["name"] for row in rows}

    def graph(self, query: str = "") -> dict[str, Any]:
        cypher = """
        MATCH (n)
        WHERE $query = ''
           OR toLower(coalesce(n.name, '')) CONTAINS toLower($query)
           OR toLower(coalesce(n.code, '')) CONTAINS toLower($query)
        WITH collect(n) AS seeds
        MATCH (a)-[r]->(b)
        WHERE $query = '' OR a IN seeds OR b IN seeds
        WITH seeds + collect(DISTINCT a) + collect(DISTINCT b) AS raw_nodes,
             collect(DISTINCT {
                source: coalesce(a.id, elementId(a)),
                target: coalesce(b.id, elementId(b)),
                relation: coalesce(r.relation, type(r))
             }) AS links
        UNWIND raw_nodes AS n
        WITH collect(DISTINCT n) AS nodes, links
        RETURN [n IN nodes | {
            id: coalesce(n.id, elementId(n)),
            name: coalesce(n.name, n.id, elementId(n)),
            category: head(labels(n)),
            code: coalesce(n.code, ''),
            symbolSize: CASE WHEN 'Course' IN labels(n) THEN 54
                             WHEN 'KnowledgePoint' IN labels(n) THEN 42
                             ELSE 32 END
        }] AS nodes,
        links
        """
        with self.driver.session() as session:
            row = session.run(cypher, query=query.strip()).single()
        return {"nodes": row["nodes"] if row else [], "links": row["links"] if row else []}

    def analysis(self) -> dict[str, Any]:
        with self.driver.session() as session:
            top_rows = session.run(
                """
                MATCH (kp:KnowledgePoint)
                OPTIONAL MATCH (kp)--(n)
                RETURN kp.id AS id, kp.name AS name, count(n) AS degree,
                       coalesce(kp.source, '') AS source
                ORDER BY degree DESC, name ASC
                LIMIT 8
                """
            )
            pair_rows = session.run(
                """
                MATCH (a:Course)-[:HAS_KNOWLEDGE_POINT]->(kp:KnowledgePoint)<-[:HAS_KNOWLEDGE_POINT]-(b:Course)
                WHERE a.id < b.id
                RETURN a.name AS left, b.name AS right, count(kp) AS count,
                       collect(kp.name) AS knowledge
                ORDER BY count DESC, left ASC, right ASC
                LIMIT 8
                """
            )
            dim_rows = session.run(
                """
                MATCH (:Course)-[:HAS_DIMENSION]->(d:DimensionValue)
                RETURN d.dimension AS dimension, d.value AS value, count(*) AS count
                ORDER BY dimension, count DESC
                """
            )
            size_row = session.run(
                "MATCH (n) WITH count(n) AS nodes MATCH ()-[r]->() RETURN nodes, count(r) AS links"
            ).single()

        dimension_counts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in dim_rows:
            dimension_counts[row["dimension"]].append({"name": row["value"], "count": row["count"]})

        return {
            "top_knowledge": [dict(row) for row in top_rows],
            "shared_pairs": [dict(row) for row in pair_rows],
            "dimension_counts": dict(dimension_counts),
            "node_count": size_row["nodes"] if size_row else 0,
            "link_count": size_row["links"] if size_row else 0,
        }


class ResilientGraphRepository:
    def __init__(self, primary: Neo4jGraphRepository, fallback: StaticGraphRepository):
        self.primary = primary
        self.fallback = fallback

    def __getattr__(self, name: str):
        primary_attr = getattr(self.primary, name)
        fallback_attr = getattr(self.fallback, name)

        def wrapped(*args, **kwargs):
            try:
                return primary_attr(*args, **kwargs)
            except Exception:
                return fallback_attr(*args, **kwargs)

        return wrapped


def build_graph_repository(config: Any):
    fallback = StaticGraphRepository(config["SAMPLE_GRAPH_PATH"])
    uri = config.get("NEO4J_URI")
    password = config.get("NEO4J_PASSWORD")
    if not uri or not password:
        if config.get("STRICT_NEO4J"):
            raise RuntimeError("NEO4J_URI and NEO4J_PASSWORD are required when STRICT_NEO4J=1.")
        return fallback
    try:
        return ResilientGraphRepository(
            Neo4jGraphRepository(uri, config.get("NEO4J_USER", "neo4j"), password),
            fallback,
        )
    except Exception:
        if config.get("STRICT_NEO4J"):
            raise
        return fallback

