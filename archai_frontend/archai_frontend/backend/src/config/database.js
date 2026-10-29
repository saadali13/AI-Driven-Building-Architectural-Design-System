import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

/**
 * Resolved PostgreSQL connection settings for ArchAI.
 * Prefer DATABASE_URL for Prisma; individual fields support raw pg pools or ops scripts.
 */
export const databaseConfig = {
  url: process.env.DATABASE_URL,
  host: process.env.DB_HOST ?? 'localhost',
  port: Number(process.env.DB_PORT ?? 5432),
  user: process.env.DB_USER ?? 'postgres',
  password: process.env.DB_PASSWORD ?? '',
  database: process.env.DB_NAME ?? 'arch_ai_db',
  schema: 'public',
};

/**
 * Build a PostgreSQL connection URL from discrete env vars (fallback).
 */
export function buildDatabaseUrl({
  host = databaseConfig.host,
  port = databaseConfig.port,
  user = databaseConfig.user,
  password = databaseConfig.password,
  database = databaseConfig.database,
  schema = databaseConfig.schema,
} = {}) {
  const encodedPassword = encodeURIComponent(password);
  return `postgresql://${user}:${encodedPassword}@${host}:${port}/${database}?schema=${schema}`;
}

/**
 * Validate that required connection settings are present.
 */
export function assertDatabaseConfig() {
  const url = databaseConfig.url || buildDatabaseUrl();

  if (!url || url.includes('YOUR_PASSWORD')) {
    throw new Error(
      'DATABASE_URL is missing or invalid. Copy backend/.env.example to backend/.env and set credentials.',
    );
  }

  if (!databaseConfig.password && !databaseConfig.url) {
    throw new Error('DB_PASSWORD (or DATABASE_URL) must be set in backend/.env');
  }

  return url;
}

export default databaseConfig;
