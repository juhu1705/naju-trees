CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    level INTEGER NOT NULL,
    pwd_hash STRING NOT NULL,
    email STRING NOT NULL,
    password_reset_token STRING,
    email_confirmed INTEGER NOT NULL,
    confirmation_token STRING
);

DROP TABLE IF EXISTS tree;
DROP TABLE IF EXISTS area;
DROP TABLE IF EXISTS tree_param;
DROP TABLE IF EXISTS tree_param_type;

CREATE TABLE tree (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER NOT NULL,
    area_id INTEGER NOT NULL,
    FOREIGN KEY (area_id) REFERENCES area (id)
);

CREATE TABLE area (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address STRING NOT NULL,
    name STRING NOT NULL,
    link STRING NOT NULL,
    short STRING NOT NULL
);

CREATE TABLE tree_param (
    tree_id INTEGER NOT NULL,
    param_id INTEGER NOT NULL,
    value STRING NOT NULL,
    PRIMARY KEY (tree_id, param_id),
    FOREIGN KEY (tree_id) REFERENCES tree (id),
    FOREIGN KEY (param_id) REFERENCES tree_param_type (id)
);

CREATE TABLE tree_param_type (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    type STRING NOT NULL,
    order_id INTEGER
);