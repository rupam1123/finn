declare namespace Cloudflare {
  interface Env {
    DB?: D1Database;
    BUCKET?: R2Bucket;
    FINN_MIGRATION_KEY?: string;
  }
}
