

/*DROP TABLE IF EXISTS Switch;
DROP TABLE IF EXISTS Temperature;
DROP TABLE IF EXISTS Motion1;
DROP TABLE IF EXISTS Motion2;
DROP TABLE IF EXISTS Image;*/


-- Create Switch table
CREATE TABLE Switch (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    status BOOLEAN NOT NULL
);

-- Create Temperature table
CREATE TABLE Temperature (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    value DECIMAL(6,2) NOT NULL
);

-- Create Motion1 table
CREATE TABLE Motion1 (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    value BOOLEAN NOT NULL
);

-- Create Motion2 table
CREATE TABLE Motion2 (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    value BOOLEAN NOT NULL
);

-- Create Image table
CREATE TABLE Image (
    id SERIAL PRIMARY KEY,
    session INTEGER NOT NULL,
    datetime TIMESTAMP NOT NULL,
    ingredient VARCHAR(1024) NOT NULL,
    style VARCHAR(32) NOT NULL
);

