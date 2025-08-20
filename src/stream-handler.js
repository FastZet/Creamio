// src/stream-handler.js

const config = require('./config');
const scrapers = require('./scrapers');
const { buildCatalog, buildSeriesMeta, buildErrorMeta, buildStream } = require('./meta-builder');
const { createCache } = require("cache-manager");
const { Keyv } = require("keyv");
const { KeyvCacheableMemory } = require("cacheable");

// Initialize a robust cache
const ttlStore = new KeyvCacheableMemory({
  ttl: config.cache.searchTTL,
  checkInterval: 24 * 60 * 60 * 1000, // Check for expired items once a day
});
const cache = createCache({
  stores: [new Keyv({ store: ttlStore })],
  ttl: config.cache.searchTTL,
});

async function handleCatalog(args) {
    const query = args.extra.search;
    if (!query) return { metas: [] };

    const cacheKey = `catalog:${query}`;
    
    return cache.wrap(cacheKey, async () => {
        console.log(`[FRESH] Scraping all sources for catalog query: "${query}"`);
        const scraperPromises = scrapers.map(scraper =>
            scraper.scrape(query).then(result => ({ ...result, sourceName: scraper.name }))
        );
        
        const results = await Promise.allSettled(scraperPromises);
        return buildCatalog(results, query);
    });
}

async function handleMeta(args) {
    const [_, sourceId, query] = args.id.split(':');
    
    const cacheKey = `meta:${sourceId}:${query}`;
    
    return cache.wrap(cacheKey, async () => {
        const source = scrapers.find(s => s.id === sourceId);
        if (!source) throw new Error(`Invalid source ID: ${sourceId}`);

        console.log(`[FRESH] Scraping "${source.name}" for meta: "${query}"`);
        const videosOrError = await source.scrape(query);

        if (videosOrError.error) {
            return buildErrorMeta(source, query, videosOrError);
        } else {
            return buildSeriesMeta(source, query, videosOrError);
        }
    });
}

function handleStream(args) {
    const [_, ...urlParts] = args.id.split('creamio:');
    const videoUrl = urlParts.join('creamio:'); // Rejoin in case URL contained 'creamio:'

    if (!videoUrl || !videoUrl.startsWith('http')) {
        return Promise.resolve({ streams: [] });
    }

    console.log(`Providing external stream for URL: ${videoUrl}`);
    return Promise.resolve(buildStream(videoUrl));
}

module.exports = { handleCatalog, handleMeta, handleStream };
