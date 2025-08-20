// src/meta-builder.js

const config = require('../config');

/**
 * Builds the catalog of sources presented to the user after a search.
 * @param {Array} scraperResults - An array of results from Promise.allSettled.
 * @param {string} query - The original search query.
 * @returns {Array} An array of Stremio meta objects for the catalog.
 */
function buildCatalog(scraperResults, query) {
    const metas = scraperResults
        .filter(result => result.status === 'fulfilled' && result.value && !result.value.error)
        .map(result => {
            // The value contains the array of videos and the sourceName
            const scraper = config.scrapers.find(s => s.name === result.value.sourceName);
            if (!scraper) return null;

            return {
                id: `creamio:${scraper.id}:${query}`,
                type: 'movie', // We present each source as a clickable "movie"
                name: `Results from ${scraper.name}`,
                poster: scraper.logo,
                description: `Search results for "${query}" from ${scraper.name}`
            };
        })
        .filter(Boolean);

    return metas;
}

/**
 * Builds the detailed "series" view for a selected source.
 * @param {object} source - The scraper source object from config.
 * @param {string} query - The search query.
 * @param {Array} videos - The array of scraped video objects.
 * @returns {object} A Stremio meta object.
 */
function buildSeriesMeta(source, query, videos) {
    const meta = {
        id: `creamio:${source.id}:${query}`,
        type: 'series',
        name: `Results for: ${query}`,
        description: `Showing top ${videos.length} results from ${source.name}`,
        poster: source.logo,
        background: config.addon.background,
        videos: videos.map((video, index) => ({
            id: `creamio:${video.url}`,
            title: video.title,
            season: 1,
            episode: index + 1,
            thumbnail: video.thumbnail,
            overview: `Duration: ${video.duration}\nSource: ${video.source}`,
            released: new Date().toISOString()
        }))
    };
    return { meta };
}

/**
 * Builds a meta object to display an error message to the user.
 * @param {object} source - The scraper source object from config.
 * @param {string} query - The search query.
 * @param {object} errorInfo - The error object from the scraper.
 * @returns {object} A Stremio meta object formatted to show an error.
 */
function buildErrorMeta(source, query, errorInfo) {
    const meta = {
        id: `creamio:error:${source.id}:${query}`,
        type: 'series',
        name: `Error: ${source.name}`,
        description: `Failed to fetch results for "${query}" from ${source.name}.`,
        poster: source.logo, // You can create a generic error version of the logo
        background: config.addon.background,
        videos: [{
            id: `creamio:error:${source.id}`,
            title: errorInfo.error || 'Scraping Failed',
            season: 1,
            episode: 1,
            overview: errorInfo.reason || 'An unknown error occurred.',
            thumbnail: 'https://raw.githubusercontent.com/username/creamio-addon/main/images/error-icon.png' // Placeholder
        }]
    };
    return { meta };
}

/**
 * Builds the stream response for a selected video.
 * @param {string} videoUrl - The direct URL to the video page.
 * @returns {object} A Stremio stream response object.
 */
function buildStream(videoUrl) {
    return {
        streams: [{
            title: 'Open in Browser',
            externalUrl: videoUrl,
            behaviorHints: {
                externalUrl: true
            }
        }]
    };
}

module.exports = {
    buildCatalog,
    buildSeriesMeta,
    buildErrorMeta,
    buildStream
};
