import { describe, it, expect } from 'vitest';
import { mapApifyPostToRawPost } from '../../packages/collectors/src/instagram.js';

describe('mapApifyPostToRawPost', () => {
  it('maps a standard Apify Instagram post to RawPost format', () => {
    const apifyPost = {
      id: '12345',
      type: 'Image',
      url: 'https://www.instagram.com/p/ABC123/',
      caption: 'Love this outfit! #ootd #streetstyle',
      hashtags: ['ootd', 'streetstyle'],
      displayUrl: 'https://example.com/image.jpg',
      images: ['https://example.com/image.jpg'],
      ownerId: '67890',
      ownerUsername: 'fashionista',
      ownerFullName: 'Fashion Lover',
      likesCount: 150,
      commentsCount: 12,
      timestamp: '2026-03-01T10:30:00.000Z',
      locationName: 'Paris, France',
    };

    const result = mapApifyPostToRawPost(apifyPost);

    expect(result.platform).toBe('instagram');
    expect(result.platformPostId).toBe('12345');
    expect(result.url).toBe('https://www.instagram.com/p/ABC123/');
    expect(result.caption).toBe('Love this outfit! #ootd #streetstyle');
    expect(result.hashtags).toEqual(['ootd', 'streetstyle']);
    expect(result.imageUrls).toEqual(['https://example.com/image.jpg']);
    expect(result.authorId).toBe('67890');
    expect(result.authorUsername).toBe('fashionista');
    expect(result.likesCount).toBe(150);
    expect(result.commentsCount).toBe(12);
    expect(result.publishedAt).toBe('2026-03-01T10:30:00.000Z');
    expect(result.mediaType).toBe('image');
    expect(result.locationName).toBe('Paris, France');
    expect(result.id).toBeDefined();
    expect(result.collectedAt).toBeDefined();
    expect(result.rawData).toEqual(apifyPost);
  });

  it('handles carousel (Sidecar) posts with multiple images', () => {
    const apifyPost = {
      id: '99999',
      type: 'Sidecar',
      url: 'https://www.instagram.com/p/XYZ/',
      caption: 'Carousel look',
      hashtags: [],
      displayUrl: 'https://example.com/img1.jpg',
      images: ['https://example.com/img1.jpg', 'https://example.com/img2.jpg'],
      ownerId: '11111',
      ownerUsername: null,
      ownerFullName: null,
      likesCount: -1,
      commentsCount: 0,
      timestamp: '2026-02-15T08:00:00.000Z',
      locationName: null,
    };

    const result = mapApifyPostToRawPost(apifyPost);
    expect(result.mediaType).toBe('carousel');
    expect(result.imageUrls).toHaveLength(2);
    expect(result.likesCount).toBe(-1);
    expect(result.authorUsername).toBeNull();
  });

  it('handles video posts', () => {
    const apifyPost = {
      id: '55555',
      type: 'Video',
      url: 'https://www.instagram.com/reel/ABC/',
      caption: 'Reel outfit check',
      hashtags: ['reels', 'fashion'],
      displayUrl: 'https://example.com/thumb.jpg',
      images: [],
      ownerId: '22222',
      ownerUsername: 'reel_queen',
      ownerFullName: 'Reel Queen',
      likesCount: 5000,
      commentsCount: 200,
      timestamp: '2026-03-05T14:00:00.000Z',
      locationName: 'Tokyo',
    };

    const result = mapApifyPostToRawPost(apifyPost);
    expect(result.mediaType).toBe('video');
    expect(result.imageUrls).toEqual(['https://example.com/thumb.jpg']);
  });

  it('handles missing fields gracefully', () => {
    const apifyPost = {
      id: '77777',
      type: undefined,
      url: undefined,
      caption: undefined,
      hashtags: undefined,
      displayUrl: undefined,
      images: undefined,
      ownerId: undefined,
      ownerUsername: undefined,
      ownerFullName: undefined,
      likesCount: undefined,
      commentsCount: undefined,
      timestamp: undefined,
      locationName: undefined,
    };

    const result = mapApifyPostToRawPost(apifyPost);
    expect(result.platform).toBe('instagram');
    expect(result.url).toBe('');
    expect(result.caption).toBe('');
    expect(result.hashtags).toEqual([]);
    expect(result.imageUrls).toEqual([]);
    expect(result.likesCount).toBe(0);
    expect(result.commentsCount).toBe(0);
    expect(result.authorUsername).toBeNull();
    expect(result.mediaType).toBe('image');
  });

  it('handles realistic unicode captions with emoji', () => {
    const apifyPost = {
      id: '88888',
      type: 'Image',
      url: 'https://www.instagram.com/p/EMOJI/',
      caption: '这件连衣裙太美了！🌸✨ Weekend vibes 💫 #穿搭 #ootd #時尚 \n\nShop link in bio 👆',
      hashtags: ['穿搭', 'ootd', '時尚'],
      displayUrl: 'https://example.com/emoji.jpg',
      images: ['https://example.com/emoji.jpg'],
      ownerId: '33333',
      ownerUsername: 'china_fashion',
      ownerFullName: '中文时尚',
      likesCount: 2500,
      commentsCount: 88,
      timestamp: '2026-03-04T09:00:00.000Z',
      locationName: '上海',
    };

    const result = mapApifyPostToRawPost(apifyPost);
    expect(result.caption).toContain('🌸');
    expect(result.caption).toContain('这件连衣裙');
    expect(result.hashtags).toContain('穿搭');
    expect(result.locationName).toBe('上海');
  });
});
