// src/scrapers/index.js

const { scrapeMetaporn } = require('./metaporn');
const { scrapePornmd } = require('./pornmd');
const config = require('../config');

// An array of all available scraper functions, mapped to their config entries.
const scrapers = [
    {
        id: 'metaporn',
        name: 'Metaporn',
        logo: config.scrapers.find(s => s.id === 'metaporn').logo,
        scrape: scrapeMetaporn
    },
    {
        id: 'pornmd',
        name: 'PornMD',
        logo: config.scrapers.find(s => s.id === 'pornmd').logo,
        scrape: scrapePornmd
    }
    // New scrapers will be added here
];

module.exports = scrapers;
