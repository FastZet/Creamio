// server.js

const express = require('express');
const path = require('path');
const { addonBuilder } = require('stremio-addon-sdk');
const manifest = require('./manifest');
const { handleCatalog, handleMeta, handleStream } = require('./src/stream-handler');

// Initialize the addon builder with the manifest
const builder = new addonBuilder(manifest);

// Define handlers for the addon's resources
builder.defineCatalogHandler(handleCatalog);
builder.defineMetaHandler(handleMeta);
builder.defineStreamHandler(handleStream);

// Get the addon's middleware handler
const addonInterface = builder.getInterface();

// --- Express App Setup ---
const app = express();

// Serve the static landing page and other files from the 'public' directory
app.use('/public', express.static(path.join(__dirname, 'public')));

// Redirect root to the landing page
app.get('/', (req, res) => {
    res.redirect('/public/index.html');
});

// Mount the Stremio addon middleware
// This will automatically handle /manifest.json, /catalog, /meta, /stream routes
app.use(addonInterface.middleware);

const PORT = process.env.PORT || 7000;

app.listen(PORT, () => {
    console.log(`Creamio addon running on port: ${PORT}`);
    console.log(`Installation link: http://127.0.0.1:${PORT}`);
});
