

/*DROP TABLE IF EXISTS Switch;
DROP TABLE IF EXISTS Temperature;
DROP TABLE IF EXISTS Motion1;
DROP TABLE IF EXISTS Motion2;
DROP TABLE IF EXISTS Image;*/


-- Create Switch table
CREATE TABLE IF NOT EXISTS Switch (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    status BOOLEAN NOT NULL
);

-- Create Temperature table
CREATE TABLE IF NOT EXISTS Temperature (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    value DECIMAL(6,2) NOT NULL
);

-- Create Motion1 table
CREATE TABLE IF NOT EXISTSMotion1 (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    value BOOLEAN NOT NULL
);

-- Create Motion2 table
CREATE TABLE IF NOT EXISTS Motion2 (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    value BOOLEAN NOT NULL
);

-- Create Image table
CREATE TABLE IF NOT EXISTS Image (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    ingredient VARCHAR(1024),
    style VARCHAR(32)
);


-- session id might be duplicated,
CREATE TABLE IF NOT EXISTS Image2 (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL, -- datetime from 1st image
    ingredient VARCHAR(1024),
    style VARCHAR(32),
    description VARCHAR(4096)
);

