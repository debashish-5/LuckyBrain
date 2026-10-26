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
    