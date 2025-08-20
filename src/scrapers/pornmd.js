// src/scrapers/pornmd.js

const axios = require('axios');
const cheerio = require('cheerio');
const config = require('../config');

/**
 * Builds a valid search URL for PornMD.
 * @param {string} query - The user's search query.
 * @returns {string} The formatted search URL.
 */
function buildUrl(query) {
    const encodedQuery = encodeURIComponent(query);
    return config.scrapers.find(s => s.id === 'pornmd').searchUrl.replace('{{query}}', encodedQuery);
}

/**
 * Scrapes PornMD for video results based on a query.
 * @param {string} query - The user's search query.
 * @returns {Promise<Array|{error: string, reason: string}>} A promise that resolves to an array of video objects or an error object.
 */
async function scrapePornmd(query) {
    const url = buildUrl(query);
    const { userAgent, timeout } = config.client;
    const selectors = config.selectors;

    try {
        const response = await axios.get(url, {
            headers: { 'User-Agent': userAgent },
            timeout: timeout
        });

        const $ = cheerio.load(response.data);

        if ($('title').text().includes('Cloudflare')) {
            console.error('PornMD scraper blocked by Cloudflare.');
            return { error: 'Scraping failed', reason: 'Blocked by Cloudflare bot protection.' };
        }

        const videos = [];
        $(selectors.resultItem).each((i, element) => {
            const el = $(element);
            const linkElement = el.find(selectors.link);

            const title = linkElement.attr('title');
            let videoUrl = linkElement.attr('href');

            if (videoUrl && videoUrl.startsWith('/out/')) {
                 const baseUrl = config.scrapers.find(s => s.id === 'pornmd').baseUrl;
                videoUrl = `${baseUrl}${videoUrl}`;
            }

            const thumbnail = el.find(selectors.thumbnail).attr('src');
            const durationText = el.find(selectors.duration).text().trim();
            
            const durationMatch = durationText.match(/\d{1,2}:\d{2}(:\d{2})?/);
            const duration = durationMatch ? durationMatch[0] : 'N/A';

            if (title && videoUrl) {
                videos.push({
                    title,
                    url: videoUrl,
                    thumbnail,
                    duration,
                    source: 'PornMD'
                });
            }
        });
        
        if (videos.length === 0) {
             return { error: 'No results found', reason: 'The search query returned no videos, or the website structure has changed.' };
        }

        return videos;

    } catch (error) {
        console.error(`Error scraping PornMD for query "${query}":`, error.message);
        return { error: 'Scraping failed', reason: `Could not connect to PornMD. The site may be down or has changed its layout. (Details: ${error.message})` };
    }
}

module.exports = { scrapePornmd };
