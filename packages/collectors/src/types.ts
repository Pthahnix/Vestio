export interface RawPost {
  id: string;
  platform: 'instagram';
  platformPostId: string;
  url: string;
  caption: string;
  hashtags: string[];
  imageUrls: string[];
  authorId: string;
  authorUsername: string | null;
  authorFullName: string | null;
  likesCount: number;
  commentsCount: number;
  publishedAt: string;
  collectedAt: string;
  mediaType: 'image' | 'video' | 'carousel';
  locationName: string | null;
  rawData: unknown;
}

export interface CollectOptions {
  hashtags?: string[];
  profiles?: string[];
  limit: number;
}

export interface CollectResult {
  posts: RawPost[];
  errors: string[];
}
