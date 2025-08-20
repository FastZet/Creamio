// src/config.js

const config = {
    // Addon general settings
    addon: {
        id: 'org.creamio.addon',
        version: '1.0.0',
        name: 'Creamio',
        description: 'Dynamic search-driven addon for adult content, creating catalogs from popular search engines.',
        logo: 'https://raw.githubusercontent.com/username/creamio-addon/main/images/logo.png', // Placeholder URL
        background: 'https://raw.githubusercontent.com/username/creamio-addon/main/images/background.png', // Placeholder URL
        resources: ['catalog', 'meta', 'stream'],
        types: ['movie', 'series'],
        idPrefixes: ['creamio:'],
        catalogs: [] // Catalogs are dynamically generated from search
    },

    // Cache settings (TTL in milliseconds)
    cache: {
        searchTTL: 7 * 24 * 60 * 60 * 1000, // 7 days
    },

    // Scraper settings
    scrapers: [
        {
            id: 'metaporn',
            name: 'Metaporn',
            logo: 'https://raw.githubusercontent.com/username/creamio-addon/main/images/metaporn-logo.png', // Placeholder
            baseUrl: 'https://www.metaporn.com',
            searchUrl: 'https://www.metaporn.com/search/{{query}}',
        },
        {
            id: 'pornmd',
            name: 'PornMD',
            logo: 'https://raw.githubusercontent.com/username/creamio-addon/main/images/pornmd-logo.png', // Placeholder
            baseUrl: 'https://www.pornmd.com',
            searchUrl: 'https://www.pornmd.com/search/{{query}}',
        },
        // Future scrapers will be added here
    ],

    // CSS selectors for parsing search results
    // Both Metaporn and PornMD use the same structure, so we can share selectors.
    selectors: {
        resultItem: 'div.card',
        link: 'a.item-title',
        title: 'a.item-title',
        thumbnail: 'img.item-image',
        duration: 'span.badge.float-right',
    },

    // HTTP client settings
    client: {
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        timeout: 8000, // 8 seconds
    }
};

module.exports = config;
