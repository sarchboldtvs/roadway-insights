-- =====================================================================
-- Pilot seed: synthetic roadway inspection data, built BY HAND, outside the
-- AI-DLC, so Pilot 1 has realistic brownfield objects to adopt.
-- Run once by a sandbox admin (SYSADMIN). All data is synthetic.
-- Creates the same shape in ROADWAY_DEV and ROADWAY_PROD (PROD gets more rows).
-- =====================================================================
USE ROLE SYSADMIN;
USE WAREHOUSE AIDLC_WH;

-- Repeat this block with DB = ROADWAY_DEV (rows 2000) and ROADWAY_PROD (rows 20000).
SET DB = 'ROADWAY_DEV';
SET N_INSPECTIONS = 2000;

CREATE DATABASE IF NOT EXISTS IDENTIFIER($DB) COMMENT = 'Pilot: created by hand (unmanaged)';
USE DATABASE IDENTIFIER($DB);
CREATE SCHEMA IF NOT EXISTS RAW;

CREATE OR REPLACE TABLE RAW.INSPECTIONS AS
SELECT
  'INS-' || LPAD(SEQ4()::STRING, 6, '0')                                   AS INSPECTION_ID,
  DATEADD(day, -UNIFORM(0, 540, RANDOM(11)), CURRENT_DATE())               AS INSPECTION_DATE,
  ARRAY_CONSTRUCT('Route 9','Main St','Elm St','Route 2','Washington St','Boylston St')[UNIFORM(0,5,RANDOM(12))]::STRING AS STREET,
  ARRAY_CONSTRUCT('1st Ave','Oak St','Pine St','Park Ave','School St')[UNIFORM(0,4,RANDOM(13))]::STRING AS CROSS_STREET,
  ARRAY_CONSTRUCT('Citizen-logged complaints','Maintenance team','Other local government agencies')[UNIFORM(0,2,RANDOM(14))]::STRING AS REQUEST_SOURCE,
  ARRAY_CONSTRUCT('Draft','Submitted','Approved','Approved','Approved','Returned')[UNIFORM(0,5,RANDOM(15))]::STRING AS STATUS,
  'inspector' || LPAD(UNIFORM(1, 40, RANDOM(16))::STRING, 3, '0') || '@example.org' AS INSPECTOR_EMAIL
FROM TABLE(GENERATOR(ROWCOUNT => $N_INSPECTIONS));

CREATE OR REPLACE TABLE RAW.ROAD_ISSUES AS
SELECT
  'ISS-' || LPAD(SEQ4()::STRING, 7, '0')                                   AS ROAD_ISSUE_ID,
  i.INSPECTION_ID,
  ARRAY_CONSTRUCT('Pothole','Crack','Damaged sign','Faded road markings','Drainage problem','Debris','Damaged guardrail','Other')[UNIFORM(0,7,RANDOM(21))]::STRING AS ISSUE_TYPE,
  UNIFORM(1, 5, RANDOM(22))                                                AS SEVERITY,
  ARRAY_CONSTRUCT(NULL,'Low','Medium','High','Urgent')[UNIFORM(0,4,RANDOM(23))]::STRING AS REPAIR_PRIORITY,
  i.INSPECTION_DATE                                                        AS LOGGED_DATE,
  UNIFORM(0, 1, RANDOM(24)) = 1                                            AS IS_OPEN
FROM RAW.INSPECTIONS i,
     TABLE(GENERATOR(ROWCOUNT => 3)) g
WHERE i.STATUS <> 'Draft' AND UNIFORM(0, 9, RANDOM(25)) < 6;

-- Hand-built view (to be adopted into DCM in Pilot 1).
CREATE OR REPLACE VIEW RAW.V_OPEN_ISSUES AS
SELECT r.*, i.STREET, i.CROSS_STREET, i.STATUS AS INSPECTION_STATUS
FROM RAW.ROAD_ISSUES r JOIN RAW.INSPECTIONS i USING (INSPECTION_ID)
WHERE r.IS_OPEN AND i.STATUS = 'Approved';

-- Classification tag on the synthetic personal column (exercises masking).
ALTER TABLE RAW.INSPECTIONS MODIFY COLUMN INSPECTOR_EMAIL
  SET TAG AIDLC_GOVERNANCE.POLICIES.CLASSIFICATION = 'restricted';

-- Ad hoc reporting role, granted by hand (a typical brownfield leftover).
USE ROLE SECURITYADMIN;
CREATE ROLE IF NOT EXISTS ROADWAY_REPORTING_ADHOC;
GRANT USAGE ON DATABASE IDENTIFIER($DB) TO ROLE ROADWAY_REPORTING_ADHOC;
GRANT USAGE ON SCHEMA IDENTIFIER($DB || '.RAW') TO ROLE ROADWAY_REPORTING_ADHOC;
GRANT SELECT ON ALL TABLES IN SCHEMA IDENTIFIER($DB || '.RAW') TO ROLE ROADWAY_REPORTING_ADHOC;

-- DEV access for agents (bootstrap section 6, applied for this project).
USE ROLE SYSADMIN;
-- run only for ROADWAY_DEV:
-- GRANT USAGE, CREATE SCHEMA ON DATABASE ROADWAY_DEV TO ROLE AIDLC_DEV_RW;
-- GRANT USAGE ON DATABASE ROADWAY_DEV TO ROLE AIDLC_DEV_RO;
-- GRANT USAGE ON SCHEMA ROADWAY_DEV.RAW TO ROLE AIDLC_DEV_RO;
-- GRANT SELECT ON ALL TABLES IN SCHEMA ROADWAY_DEV.RAW TO ROLE AIDLC_DEV_RO;
-- GRANT SELECT ON ALL VIEWS  IN SCHEMA ROADWAY_DEV.RAW TO ROLE AIDLC_DEV_RO;
-- GRANT USAGE, CREATE SCHEMA ON DATABASE ROADWAY_DEV TO ROLE AIDLC_DEV_RW;   -- DCM project owner
-- PROD read for agents goes through terraform/access/roadway.tf (Pilot 1 tests that gate).
