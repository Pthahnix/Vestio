import { randomUUID } from 'node:crypto';
import { ApifyClient } from 'apify-client';
import type { RawPost, CollectOptions, CollectResult } from './types.js';

function mapMediaType(apifyType: string): RawPost['mediaType'] {
  switch (apifyType) {
    case 'Video': return 'video';
    case 'Sidecar': return 'carousel';
    default: return 'image';
  }
}

export function mapApifyPostToRawPost(apifyPost: Record<string, any>): RawPost {
  return {
    id: randomUUID(),
    platform: 'instagram',
    platformPostId: String(apifyPost.id),
    url: apifyPost.url ?? '',
    caption: apifyPost.caption ?? '',
    hashtags: apifyPost.hashtags ?? [],
    imageUrls: apifyPost.images?.length
      ? apifyPost.images
      : apifyPost.displayUrl
        ? [apifyPost.displayUrl]
        : [],
    authorId: String(apifyPost.ownerId ?? ''),
    authorUsername: apifyPost.ownerUsername ?? null,
    authorFullName: apifyPost.ownerFullName ?? null,
    likesCount: apifyPost.likesCount ?? 0,
    commentsCount: apifyPost.commentsCount ?? 0,
    publishedAt: apifyPost.timestamp ?? new Date().toISOString(),
    collectedAt: new Date().toISOString(),
    mediaType: mapMediaType(apifyPost.type ?? 'Image'),
    locationName: apifyPost.locationName ?? null,
    rawData: apifyPost,
  };
}

export async function collectInstagram(
  options: CollectOptions,
  apifyToken: string,
): Promise<CollectResult> {
  const client = new ApifyClient({ token: apifyToken });
  const posts: RawPost[] = [];
  const errors: string[] = [];

  const directUrls: string[] = [];
  for (const tag of options.hashtags ?? []) {
    directUrls.push(`https://www.instagram.com/explore/tags/${tag}`);
  }
  for (const profile of options.profiles ?? []) {
    const handle = profile.startsWith('@') ? profile.slice(1) : profile;
    directUrls.push(`https://www.instagram.com/${handle}/`);
  }

  if (directUrls.length === 0) {
    return { posts: [], errors: ['No hashtags or profiles provided'] };
  }

  try {
    const run = await client.actor('apify/instagram-scraper').call({
      directUrls,
      resultsType: 'posts',
      resultsLimit: options.limit,
    });

    const { items } = await client
      .dataset(run.defaultDatasetId)
      .listItems();

    for (const item of items) {
      try {
        posts.push(mapApifyPostToRawPost(item));
      } catch (err) {
        errors.push(`Failed to map post ${item.id}: ${err}`);
      }
    }
  } catch (err) {
    errors.push(`Apify actor run failed: ${err}`);
  }

  return { posts, errors };
}
