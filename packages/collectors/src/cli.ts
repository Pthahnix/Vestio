import { writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';
import { collectInstagram } from './instagram.js';
import type { CollectOptions } from './types.js';

async function main() {
  const args = process.argv.slice(2);

  const hashtags: string[] = [];
  const profiles: string[] = [];
  let limit = 100;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--hashtags' && args[i + 1]) {
      hashtags.push(...args[i + 1].split(','));
      i++;
    } else if (args[i] === '--profiles' && args[i + 1]) {
      profiles.push(...args[i + 1].split(','));
      i++;
    } else if (args[i] === '--limit' && args[i + 1]) {
      limit = parseInt(args[i + 1], 10);
      i++;
    }
  }

  const token = process.env.TOKEN_APIFY;
  if (!token) {
    console.error('Error: TOKEN_APIFY environment variable is required');
    process.exit(1);
  }

  console.log(`Collecting from Instagram: hashtags=${hashtags}, profiles=${profiles}, limit=${limit}`);

  const options: CollectOptions = { hashtags, profiles, limit };
  const result = await collectInstagram(options, token);

  const outDir = join(process.cwd(), '..', '..', 'data', 'raw');
  mkdirSync(outDir, { recursive: true });

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const outPath = join(outDir, `instagram-${timestamp}.json`);
  writeFileSync(outPath, JSON.stringify(result.posts, null, 2));

  console.log(`Collected ${result.posts.length} posts → ${outPath}`);
  if (result.errors.length > 0) {
    console.warn(`Errors (${result.errors.length}):`, result.errors);
  }
}

main().catch(console.error);
