CREATE TABLE api_job_budget(requested_at TEXT NOT NULL);
--> statement-breakpoint
CREATE TABLE attempts(
                    id INTEGER PRIMARY KEY, kind TEXT, symbol TEXT, started_at TEXT,
                    finished_at TEXT, status TEXT, details TEXT);
--> statement-breakpoint
CREATE TABLE filing_versions(
                    id TEXT, revision INTEGER, symbol TEXT, observed_at TEXT,
                    published_at TEXT, content_hash TEXT, payload TEXT, PRIMARY KEY(id,revision));
--> statement-breakpoint
CREATE TABLE filings(
                    id TEXT PRIMARY KEY, symbol TEXT, published_at TEXT, payload TEXT);
--> statement-breakpoint
CREATE TABLE http_cache(url TEXT PRIMARY KEY, payload TEXT);
--> statement-breakpoint
CREATE TABLE pull_jobs(id TEXT PRIMARY KEY,symbol TEXT,status TEXT,updated_at TEXT,payload TEXT);
--> statement-breakpoint
CREATE TABLE raw_responses(
                    sha256 TEXT PRIMARY KEY, url TEXT, fetched_at TEXT, body BLOB);
--> statement-breakpoint
CREATE TABLE runs(
                    id INTEGER PRIMARY KEY, started_at TEXT, payload TEXT);
--> statement-breakpoint
CREATE TABLE schema_version(version INTEGER PRIMARY KEY);
--> statement-breakpoint
CREATE TABLE snapshots(
                    kind TEXT, symbol TEXT, fetched_at TEXT, payload TEXT,
                    PRIMARY KEY(kind,symbol));
--> statement-breakpoint
CREATE INDEX attempts_source ON attempts(kind,symbol,id);
--> statement-breakpoint
CREATE INDEX filing_window ON filing_versions(symbol,published_at,observed_at);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS read_documents(path TEXT PRIMARY KEY,status INTEGER NOT NULL,body TEXT NOT NULL);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS read_cards(id TEXT,revision INTEGER,symbol TEXT,published_at TEXT,observed_at TEXT,state_at TEXT,processed INTEGER,payload TEXT,PRIMARY KEY(id,revision,state_at));
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS read_sessions(id TEXT PRIMARY KEY,symbol TEXT,cutoff TEXT,snapshot_at TEXT,payload TEXT,detail TEXT);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS read_quotes(sha256 TEXT,page INTEGER,quote_id TEXT,payload TEXT,PRIMARY KEY(sha256,page,quote_id));
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS raw_objects(sha256 TEXT PRIMARY KEY,size INTEGER,is_pdf INTEGER);
--> statement-breakpoint
CREATE TABLE IF NOT EXISTS read_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);

--> statement-breakpoint
CREATE TABLE IF NOT EXISTS imported_objects(sha256 TEXT PRIMARY KEY,size INTEGER NOT NULL);
