// src/stream-handler.js

const config = require('./config');
const scrapers = require('./scrapers');
const { buildCatalog, buildSeriesMeta, buildErrorMeta, buildStream } = require('./meta-builder');

// A simple in-memory cache for this example.
// For a production app, this should be replaced with a more robust solution like the one in `tmdb-collections`.
const cache = new Map();

function getCache(key) {
    const entry = cache.get(key);
    if (entry && entry.expiry > Date.now()) {
        console.log(`[CACHE HIT] for key: ${key}`);
        return entry.value;
    }
    console.log(`[CACHE MISS] for key: ${key}`);
    return null;
}

function setCache(key, value, ttl) {
    const expiry = Date.now() + ttl;
    cache.set(key, { value, expiry });
    console.log(`[CACHE SET] for key: ${key} with TTL: ${ttl}ms`);
}


// --- Route Handlers ---

async function handleCatalog(args) {
    const query = args.extra.search;
    if (!query) {
        return { metas: [] };
    }

    const cacheKey = `catalog:${query}`;
    const cached = getCache(cacheKey);
    if (cached) return { metas: cached };
    
    console.log(`Scraping all sources for query: "${query}"`);

    const scraperPromises = scrapers.map(scraper => 
        scraper.scrape(query).then(result => {
            // Attach the scraper's name to valid results for easier identification
            if (result && !result.error) {
                return { ...result, sourceName: scraper.name };
            }
            return result;
        })
    );

    const results = await Promise.allSettled(scraperPromises);

    const metas = buildCatalog(results, query);
    
    setCache(cacheKey, metas, config.cache.searchTTL);

    return { metas };
}


async function handleMeta(args) {
    const [_, sourceId, query] = args.id.split(':');
    
    const cacheKey = `meta:${sourceId}:${query}`;
    const cached = getCache(cacheKey);
    if (cached) return cached;

    const source = scrapers.find(s => s.id === sourceId);
    if (!source) {
        throw new Error(`Invalid source ID: ${sourceId}`);
    }

    console.log(`Scraping "${source.name}" for meta: "${query}"`);
    const videosOrError = await source.scrape(query);

    let metaResponse;
    if (videosOrError.error) {
        metaResponse = buildErrorMeta(source, query, videosOrError);
    } else {
        metaResponse = buildSeriesMeta(source, query, videosOrError);
    }
    
    setCache(cacheKey, metaResponse, config.cache.searchTTL);

    return metaResponse;
}


function handleStream(args) {
    const [_, videoUrl] = args.id.split('creamio:');

    if (!videoUrl || !videoUrl.startsWith('http')) {
        return { streams: [] };
    }

    console.log(`Providing external stream for URL: ${videoUrl}`);
    return Promise.resolve(buildStream(videoUrl));
}


module.exports = { handleCatalog, handleMeta, handleStream };
