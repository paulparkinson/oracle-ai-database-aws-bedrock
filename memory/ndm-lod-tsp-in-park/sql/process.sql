-- ============================================================================
-- Theme Park Network Data Model Setup
--
-- Purpose:
--   Build an Oracle Spatial Network Data Model (NDM) network after the
--   following source tables have been imported from GeoJSON:
--
--     THEME_PARK_NETWORK_NODES
--     THEME_PARK_NETWORK_LINKS
--
-- Source table expectations:
--   THEME_PARK_NETWORK_NODES
--     NODE_ID NUMBER
--     NAME    VARCHAR2
--     NODE_TYPE VARCHAR2
--     GEOM    MDSYS.SDO_GEOMETRY (Point, SRID 4326)
--
--   THEME_PARK_NETWORK_LINKS
--     LINK_ID       NUMBER
--     START_NODE_ID NUMBER
--     END_NODE_ID   NUMBER
--     NAME          VARCHAR2
--     LINK_TYPE     VARCHAR2
--     ACCESSIBLE    VARCHAR2
--     COVERED       VARCHAR2
--     GEOM          MDSYS.SDO_GEOMETRY (LineString, SRID 4326)
--
-- Result:
--   THEME_PARK_NET, a one-level, undirected spatial network with:
--     - link COST populated with geometry length in meters
--     - ACCESSIBLE and COVERED registered as link user data
--
-- Notes:
--   1. Run this script as the schema owner of the source tables.
--   2. This script is intended for a fresh THEME_PARK_NET setup.
--   3. Do not run the script again after the network has been populated unless
--      the existing THEME_PARK_NET objects and metadata have been removed.
--   4. The network uses link length as COST. For time-based routing, replace
--      COST with walking time in seconds.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Validate source row counts and geometry types
-- ----------------------------------------------------------------------------

SELECT COUNT(*) AS node_count
FROM theme_park_network_nodes;

SELECT COUNT(*) AS link_count
FROM theme_park_network_links;

SELECT n.geom.sdo_gtype,
       n.geom.sdo_srid,
       COUNT(*) AS row_count
FROM theme_park_network_nodes n
GROUP BY n.geom.sdo_gtype, n.geom.sdo_srid;

SELECT l.geom.sdo_gtype,
       l.geom.sdo_srid,
       COUNT(*) AS row_count
FROM theme_park_network_links l
GROUP BY l.geom.sdo_gtype, l.geom.sdo_srid;

-- Expected source geometry:
--   Nodes: 2001 / 4326
--   Links: 2002 / 4326

-- ----------------------------------------------------------------------------
-- 2. Validate link endpoint references
-- ----------------------------------------------------------------------------

SELECT COUNT(*) AS invalid_links
FROM theme_park_network_links l
WHERE NOT EXISTS (
    SELECT 1
    FROM theme_park_network_nodes n
    WHERE n.node_id = l.start_node_id
)
OR NOT EXISTS (
    SELECT 1
    FROM theme_park_network_nodes n
    WHERE n.node_id = l.end_node_id
);

-- Expected result: 0

-- ----------------------------------------------------------------------------
-- 3. Create the empty Oracle Spatial Network Data Model network
-- ----------------------------------------------------------------------------

-- This setup creates a one-level, undirected spatial network.
-- node_with_cost = TRUE creates a COST column in the node table.

BEGIN
    SDO_NET.CREATE_SDO_NETWORK(
        network                 => 'THEME_PARK_NET',
        no_of_hierarchy_levels => 1,
        is_directed             => FALSE,
        node_with_cost          => TRUE
    );
END;
/

-- ----------------------------------------------------------------------------
-- 4. Load source nodes into the NDM node table
-- ----------------------------------------------------------------------------

-- NODE_ID is the numeric ID generated from the original string feature ID.
-- NODE_NAME and NODE_TYPE are truncated to the target column size.
-- ACTIVE = 'Y' makes every node active in network analysis.
-- Node COST is set to zero; the initial routing cost is carried by links.

INSERT INTO theme_park_net_node$ (
    node_id,
    node_name,
    node_type,
    active,
    geometry,
    cost
)
SELECT
    node_id,
    SUBSTR(NVL(name, 'NODE_' || TO_CHAR(node_id)), 1, 200),
    SUBSTR(NVL(node_type, 'walkway'), 1, 200),
    'Y',
    geom,
    0
FROM theme_park_network_nodes;

-- ----------------------------------------------------------------------------
-- 5. Load source links into the NDM link table
-- ----------------------------------------------------------------------------

-- START_NODE_ID and END_NODE_ID define link connectivity.
-- LINK_LEVEL = 1 because this demo has one network hierarchy level.
-- COST is initially set to 1 and is replaced with link length in Section 6.
-- Original string IDs and parent-link attributes remain in the source table.

INSERT INTO theme_park_net_link$ (
    link_id,
    link_name,
    start_node_id,
    end_node_id,
    link_type,
    active,
    link_level,
    geometry,
    cost
)
SELECT
    link_id,
    SUBSTR(NVL(name, 'LINK_' || TO_CHAR(link_id)), 1, 200),
    start_node_id,
    end_node_id,
    SUBSTR(NVL(link_type, 'walkway'), 1, 200),
    'Y',
    1,
    geom,
    1
FROM theme_park_network_links;

-- ----------------------------------------------------------------------------
-- 6. Use link geometry length as link COST
-- ----------------------------------------------------------------------------

-- The source geometry uses SRID 4326. For geodetic data, Oracle returns
-- SDO_LENGTH in meters when the unit is specified as unit=M.

UPDATE theme_park_net_link$ l
SET l.cost = SDO_GEOM.SDO_LENGTH(
                 l.geometry,
                 0.05,
                 'unit=M'
             )
WHERE l.geometry IS NOT NULL;

-- ----------------------------------------------------------------------------
-- 7. Add link-level user data columns
-- ----------------------------------------------------------------------------

-- These columns store application attributes that are not connectivity fields.

ALTER TABLE theme_park_net_link$
ADD (
    accessible VARCHAR2(10),
    covered    VARCHAR2(10)
);

-- ----------------------------------------------------------------------------
-- 8. Copy ACCESSIBLE and COVERED from the source link table
-- ----------------------------------------------------------------------------

MERGE INTO theme_park_net_link$ t
USING (
    SELECT
        link_id,
        accessible,
        covered
    FROM theme_park_network_links
) s
ON (t.link_id = s.link_id)
WHEN MATCHED THEN
    UPDATE SET
        t.accessible = s.accessible,
        t.covered    = s.covered;

-- ----------------------------------------------------------------------------
-- 9. Register link user data for the NDM LOD API
-- ----------------------------------------------------------------------------

-- Registration tells the default LOD user-data I/O implementation to load
-- these columns into the Java Link user-data representation.

INSERT INTO user_sdo_network_user_data (
    network,
    table_type,
    data_name,
    data_type,
    data_length,
    category_id
)
VALUES (
    'THEME_PARK_NET',
    'LINK',
    'ACCESSIBLE',
    'VARCHAR2',
    10,
    0
);

INSERT INTO user_sdo_network_user_data (
    network,
    table_type,
    data_name,
    data_type,
    data_length,
    category_id
)
VALUES (
    'THEME_PARK_NET',
    'LINK',
    'COVERED',
    'VARCHAR2',
    10,
    0
);

UPDATE user_sdo_network_metadata
SET user_defined_data = 'Y'
WHERE network = 'THEME_PARK_NET';

-- ----------------------------------------------------------------------------
-- 10. Register spatial metadata for NDM geometry tables
-- ----------------------------------------------------------------------------

-- The path table is empty initially, but its geometry metadata is required
-- for network validation.

INSERT INTO user_sdo_geom_metadata (
    table_name,
    column_name,
    diminfo,
    srid
)
VALUES (
    'THEME_PARK_NET_NODE$',
    'GEOMETRY',
    SDO_DIM_ARRAY(
        SDO_DIM_ELEMENT('Longitude', -180, 180, 0.000001),
        SDO_DIM_ELEMENT('Latitude',  -90,  90, 0.000001)
    ),
    4326
);

INSERT INTO user_sdo_geom_metadata (
    table_name,
    column_name,
    diminfo,
    srid
)
VALUES (
    'THEME_PARK_NET_LINK$',
    'GEOMETRY',
    SDO_DIM_ARRAY(
        SDO_DIM_ELEMENT('Longitude', -180, 180, 0.000001),
        SDO_DIM_ELEMENT('Latitude',  -90,  90, 0.000001)
    ),
    4326
);

INSERT INTO user_sdo_geom_metadata (
    table_name,
    column_name,
    diminfo,
    srid
)
VALUES (
    'THEME_PARK_NET_PATH$',
    'GEOMETRY',
    SDO_DIM_ARRAY(
        SDO_DIM_ELEMENT('Longitude', -180, 180, 0.000001),
        SDO_DIM_ELEMENT('Latitude',  -90,  90, 0.000001)
    ),
    4326
);

-- ----------------------------------------------------------------------------
-- 11. Create spatial indexes on the NDM node and link tables
-- ----------------------------------------------------------------------------

CREATE INDEX theme_park_net_node_sidx
ON theme_park_net_node$(geometry)
INDEXTYPE IS MDSYS.SPATIAL_INDEX_V2;

CREATE INDEX theme_park_net_link_sidx
ON theme_park_net_link$(geometry)
INDEXTYPE IS MDSYS.SPATIAL_INDEX_V2;

-- ----------------------------------------------------------------------------
-- 12. Commit and validate the completed network
-- ----------------------------------------------------------------------------

COMMIT;

SELECT COUNT(*) AS ndm_node_count
FROM theme_park_net_node$;

SELECT COUNT(*) AS ndm_link_count
FROM theme_park_net_link$;

SELECT MIN(cost) AS min_link_cost_m,
       MAX(cost) AS max_link_cost_m,
       AVG(cost) AS avg_link_cost_m,
       COUNT(*) AS link_count
FROM theme_park_net_link$;

SELECT network,
       user_defined_data
FROM user_sdo_network_metadata
WHERE network = 'THEME_PARK_NET';

SELECT network,
       table_type,
       data_name,
       data_type,
       data_length,
       category_id
FROM user_sdo_network_user_data
WHERE network = 'THEME_PARK_NET'
ORDER BY category_id, data_name;

SELECT SDO_NET.VALIDATE_NETWORK('THEME_PARK_NET') AS validation_result
FROM dual;

-- Expected validation result: TRUE
