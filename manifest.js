// manifest.js

const config = require('./src/config');

const manifest = {
    ...config.addon,
    catalogs: [
        {
            type: 'movie',
            id: 'creamio.search',
            name: 'Creamio Search',
            extra: [{ name: 'search', isRequired: true }]
        }
    ]
};

module.exports = manifest;
