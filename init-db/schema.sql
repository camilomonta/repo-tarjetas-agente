CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE tarjetas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    color TEXT NOT NULL CHECK (color IN ('verde', 'amarilla', 'roja')),
    cantidad INTEGER NOT NULL DEFAULT 0,
    UNIQUE (usuario_id, color)
);
