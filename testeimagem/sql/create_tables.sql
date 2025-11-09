-- Schema base para o fluxo de alertas IOT

CREATE TABLE IF NOT EXISTS register (
    id SERIAL PRIMARY KEY,
    integration_id TEXT NOT NULL UNIQUE,
    device_name TEXT NOT NULL,
    location TEXT,
    callback_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE register IS 'Dispositivos registrados no simulador IOT';

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    integration_id TEXT NOT NULL,
    raw_payload JSONB NOT NULL,
    triage JSONB,
    triage_level TEXT,
    resumo TEXT,
    is_alarm BOOLEAN NOT NULL DEFAULT FALSE,
    status TEXT NOT NULL DEFAULT 'processado',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_events_register
        FOREIGN KEY (integration_id)
        REFERENCES register (integration_id)
        ON DELETE SET NULL
);

COMMENT ON TABLE events IS 'Eventos processados pela IA armazenados para geração de relatórios';

CREATE INDEX IF NOT EXISTS idx_events_integration ON events (integration_id);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_events_alarm_status ON events (is_alarm, status);


