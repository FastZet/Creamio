// src/stream-handler.js
const config = require('./config');
const scrapers = require('./scrapers');
const { buildCatalog, buildSeriesMeta, buildErrorMeta, buildStream } = require('./meta-builder');

console.log('📦 Stream handler module loading...');
console.log('🔧 Available scrapers:', scrapers.map(s => s.name));

// Simple in-memory cache to avoid version conflicts
const simpleCache = new Map();

console.log('💾 Simple cache initialized');

async function handleCatalog(args) {
    console.log('🎯 handleCatalog called with args:', JSON.stringify(args, null, 2));
    
    const query = args.extra?.search;
    console.log('🔍 Extracted search query:', query);
    
    if (!query) {
        console.log('❌ No search query provided, returning empty metas');
        return { metas: [] };
    }

    const cacheKey = `catalog:${query}`;
    console.log('🔑 Cache key:', cacheKey);

    // Check simple cache first
    if (simpleCache.has(cacheKey)) {
        console.log('✅ Cache hit for:', cacheKey);
        return simpleCache.get(cacheKey);
    }

    console.log(`🆕 [FRESH] Scraping all sources for catalog query: "${query}"`);
    console.log(`🕷️ Starting scraper promises for ${scrapers.length} scrapers...`);
    
    const scraperPromises = scrapers.map(scraper => {
        console.log(`🎯 Starting scraper: ${scraper.name}`);
        return scraper.scrape(query)
            .then(result => {
                console.log(`✅ Scraper ${scraper.name} completed:`, result?.error ? 'ERROR' : `${result?.length || 0} results`);
                return { ...result, sourceName: scraper.name };
            })
            .catch(error => {
                console.error(`❌ Scraper ${scraper.name} failed:`, error.message);
                return { error: error.message, sourceName: scraper.name };
            });
    });

    const results = await Promise.allSettled(scraperPromises);
    console.log('🏁 All scrapers completed. Results:', results.length);
    
    results.forEach((result, index) => {
        const scraperName = scrapers[index].name;
        console.log(`📊 ${scraperName} result:`, result.status, result.value?.error || 'OK');
    });

    const catalog = buildCatalog(results, query);
    console.log('📚 Built catalog with', catalog?.length || 0, 'items');
    
    const finalResult = { metas: catalog };
    
    // Store in simple cache with TTL (expire after 1 hour)
    simpleCache.set(cacheKey, finalResult);
    setTimeout(() => {
        simpleCache.delete(cacheKey);
        console.log('🗑️ Cache entry expired:', cacheKey);
    }, 60 * 60 * 1000); // 1 hour
    
    return finalResult;
}

async function handleMeta(args) {
    console.log('📖 handleMeta called with args:', JSON.stringify(args, null, 2));
    
    const [_, sourceId, query] = args.id.split(':');
    console.log('🔍 Parsed - sourceId:', sourceId, 'query:', query);
    
    const cacheKey = `meta:${sourceId}:${query}`;

    // Check simple cache first
    if (simpleCache.has(cacheKey)) {
        console.log('✅ Cache hit for:', cacheKey);
        return simpleCache.get(cacheKey);
    }

    const source = scrapers.find(s => s.id === sourceId);
    if (!source) {
        console.error('❌ Invalid source ID:', sourceId);
        throw new Error(`Invalid source ID: ${sourceId}`);
    }

    console.log(`🆕 [FRESH] Scraping "${source.name}" for meta: "${query}"`);

    const videosOrError = await source.scrape(query);
    
    let result;
    if (videosOrError.error) {
        console.log('❌ Scraper returned error:', videosOrError.error);
        result = buildErrorMeta(source, query, videosOrError);
    } else {
        console.log('✅ Scraper returned', videosOrError.length, 'videos');
        result = buildSeriesMeta(source, query, videosOrError);
    }

    // Store in simple cache
    simpleCache.set(cacheKey, result);
    setTimeout(() => {
        simpleCache.delete(cacheKey);
        console.log('🗑️ Cache entry expired:', cacheKey);
    }, 60 * 60 * 1000); // 1 hour

    return result;
}

function handleStream(args) {
    console.log('🎬 handleStream called with args:', JSON.stringify(args, null, 2));
    
    const [_, ...urlParts] = args.id.split('creamio:');
    const videoUrl = urlParts.join('creamio:'); // Rejoin in case URL contained 'creamio:'

    if (!videoUrl || !videoUrl.startsWith('http')) {
        console.log('❌ Invalid video URL:', videoUrl);
        return Promise.resolve({ streams: [] });
    }

    console.log('✅ Providing external stream for URL:', videoUrl);
    return Promise.resolve(buildStream(videoUrl));
}

console.log('📦 Stream handler module loaded successfully');

module.exports = {
    handleCatalog,
    handleMeta,
    handleStream
};
