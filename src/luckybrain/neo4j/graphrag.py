from neo4j import GraphDatabase, RoutingControl
import os 
import re

_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

def _safe(name): 
    """Labels, relationship types and property names go into the query text
    (they can't be parameters), so only allow plain identifiers."""
    if not isinstance(name, str) or not _NAME.match(name): 
        raise ValueError(f"Invalid Name {name!r}: use letters, digits and _ only")
    return f" `{name}`"



class Neo4jGraph: 
    def __init__(self, uri = None, password= None, database=None): 
        uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = user or os.getenv("NEO4J_USER", "neo4j")
        password = password or os.getenv("NEO4J_PASSWORD")
        if not password: 
            raise ValueError("Password missing: pass password=... or set NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE","neo4j")
        self.driver = GraphDatabase.driver(uri=uri, auth=(user, password))
        self.driver.verify_connectivity()  # fail early if usr give wrong details


    def close(self): 
        self.driver.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc): 
        self.close()

    def _execute(self,cypher = None, params=None, write = False): 
        records, summary,_ = self.driver.execute_query(
            cypher, 
            parameters_=params, 
            database_=self.database, 
            routing_=RoutingControl.WRITE if write else RoutingControl.READ
        )
        return records,summary

    def query(self,cypher, params=None, write= False): 
        """Run any Cypher. Always pass values through params, never f-strings."""
        records, _ = self._execute(cypher=cypher, params=params, write=write)
        return [r.data() for r in records]

    def add_node(self,label,properties, key=None): 
        """key=None always creates a new node.
        key="name" updates the existing node with that name, or creates it (no duplicates)."""
        L = _safe(label)
        if key: 
            if key not in properties: 
                raise ValueError(f"Key {key!r} must be in properties")
            cypher = (f"MERGE (n:{L} {{{_safe(key)}:$key_value}})"
                      "SET n += $props RETURN properties(n) AS node")
            params = {'key_value':properties[key], 'props':properties}

        else: 
            cypher = f"CREATE (n:{L}) SET n+=$props RETURN properties(n) AS node"
            params = {'props':properties}
        return self.query(cypher=cypher, params=params,write=True)[0]['node']



    def add_nodes(self,label,rows, key): 
        """Add many nodes at once (fast). rows = list of property dicts."""
        L,K = _safe(label), _safe(key)
        if any(key not in r for r in rows): 
            raise ValueError(f"Every row needs the key : {key!r}")
        if not rows: 
            return 0
        cypher = (f"UNWIND $rows AS row MERGE (n:{L} {{{K}: row.{K}}}) SET n += row")
        _,summary = self._execute(cypher, {'rows':rows}, write=True)
        return len(rows)

    def add_relationship(self,start, rel_type, end, properties = None): 
        """start / end = (label, key, value).
        add_relationship(("Person","name","Alice"), "KNOWS", ("Person","name","Bob"), {"since": 2020})"""
        (al,ak,av),(bl,bk,bv) = start, end
        cypher = (
            f"MATCH (a:{_safe(al)} {{{_safe(ak)}: $a_val}}), (b:{_safe(bl)} {{{_safe(bk)}: $b_val}}) "
            f"MERGE (a)-[r:{_safe(rel_type)}]->(b) SET r += $props RETURN type(r) AS type"
        )
        rows = self.query(cypher, {"a_val": av, "b_val": bv, "props": properties or {}}, write=True)
        if not rows:
            raise LookupError("One or both nodes not found. Add the nodes first.")
        return True


    # ---------- retrieve ----------
    def get_node(self, label, key, value):
        rows = self.query(
            f"MATCH (n:{_safe(label)} {{{_safe(key)}: $v}}) RETURN properties(n) AS node LIMIT 1",
            {"v": value})
        return rows[0]["node"] if rows else None

    def find_nodes(self, label, where=None, limit=25):
        """where = {"city": "Pune", "age": 30} means all conditions must match."""
        conds, params = [], {"limit": limit}
        for i, (k, v) in enumerate((where or {}).items()):
            conds.append(f"n.{_safe(k)} = $w{i}")
            params[f"w{i}"] = v
        where_sql = "WHERE " + " AND ".join(conds) if conds else ""
        rows = self.query(
            f"MATCH (n:{_safe(label)}) {where_sql} RETURN properties(n) AS node LIMIT $limit", params)
        return [r["node"] for r in rows]

    def search(self, label, key, text, limit=25):
        """Case-insensitive 'contains' search on one property."""
        rows = self.query(
            f"MATCH (n:{_safe(label)}) WHERE toLower(toString(n.{_safe(key)})) CONTAINS toLower($t) "
            "RETURN properties(n) AS node LIMIT $limit", {"t": text, "limit": limit})
        return [r["node"] for r in rows]

    def neighbors(self, label, key, value, rel_type=None, direction="both", limit=25):
        """Nodes connected to one node. direction: "out", "in" or "both"."""
        if direction not in ("out", "in", "both"):
            raise ValueError("direction must be 'out', 'in' or 'both'")
        rel = f"[r:{_safe(rel_type)}]" if rel_type else "[r]"
        pattern = {"out": f"(n)-{rel}->(m)", "in": f"(n)<-{rel}-(m)", "both": f"(n)-{rel}-(m)"}[direction]
        return self.query(
            f"MATCH (n:{_safe(label)} {{{_safe(key)}: $v}}) MATCH {pattern} "
            "RETURN type(r) AS relationship, labels(m) AS labels, properties(m) AS node LIMIT $limit",
            {"v": value, "limit": limit})

    # ---------- update / delete ----------
    def update_node(self, label, key, value, properties):
        rows = self.query(
            f"MATCH (n:{_safe(label)} {{{_safe(key)}: $v}}) SET n += $props RETURN properties(n) AS node",
            {"v": value, "props": properties}, write=True)
        if not rows:
            raise LookupError(f"{label} with {key}={value!r} not found")
        return rows[0]["node"]

    def delete_node(self, label, key, value):
        """Deletes the node and all its relationships. Returns how many nodes were deleted."""
        _, summary = self._execute(
            f"MATCH (n:{_safe(label)} {{{_safe(key)}: $v}}) DETACH DELETE n", {"v": value}, write=True)
        return summary.counters.nodes_deleted

    # ---------- setup / info ----------
    def create_unique_constraint(self, label, key):
        """Do this once per label. Prevents duplicates and makes MERGE fast."""
        self._execute(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{_safe(label)}) REQUIRE n.{_safe(key)} IS UNIQUE",
            write=True)

    def schema(self):
        labels = [r["label"] for r in self.query("CALL db.labels() YIELD label RETURN label")]
        rels = [r["relationshipType"] for r in
                self.query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")]
        nodes = self.query("MATCH (n) RETURN count(n) AS c")[0]["c"]
        edges = self.query("MATCH ()-[r]->() RETURN count(r) AS c")[0]["c"]
        return {"labels": labels, "relationship_types": rels, "nodes": nodes, "relationships": edges}