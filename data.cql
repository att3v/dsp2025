--Cassandra schemas for different threat intelligence data

CREATE KEYSPACE IF NOT EXISTS threat_intelligence
WITH replication = {'class': 'NetworkTopologyStrategy', 'dc1': 3};

USE threat_intelligence;

--Table for IoCs
CREATE TABLE iocs (
    id UUID PRIMARY KEY,
    type TEXT,
    value TEXT,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    source TEXT,
    tags SET<TEXT>
);

--Table for Threat actors
CREATE TABLE threat_actors (
    id UUID PRIMARY KEY,
    name TEXT,
    activities TEXT,
    country TEXT,
    associated_iocs SET<UUID>  -- Links to IoCs
);

--Table for malware
CREATE TABLE malware (
    id UUID PRIMARY KEY,
    name TEXT,
    description TEXT,
    type TEXT,
    associated_iocs SET<UUID>  -- Links to IoCs
);

--Table for vulnerabilities
CREATE TABLE vulnerabilities (
    id UUID PRIMARY KEY,
    baseScore DECIMAL,
    cve TEXT,
    description TEXT,
    lastModified TIMESTAMP,
    severity TEXT,
    source TEXT,
    status TEXT,
    timestamp TIMESTAMP
);

--Table for incidents
CREATE TABLE incidents (
    id UUID PRIMARY KEY,
    date TIMESTAMP,
    type TEXT,
    description TEXT,
    involved_iocs SET<UUID>  -- Links to IoCs
);

--Table for feeds
CREATE TABLE feeds (
    id UUID PRIMARY KEY,
    name TEXT,
    source_url TEXT,
    last_updated TIMESTAMP,
    intelligence_type TEXT
);
