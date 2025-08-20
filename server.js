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

// Get the addon interface, which is an Express router
const addonInterface = builder.getInterface();

// --- Express App Setup ---
const app = express();

// Serve the static landing page from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Serve the manifest directly at the root
app.get('/manifest.json', (req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');
    res.send(manifest);
});

// Mount the Stremio addon interface
app.use('/', addonInterface);

const PORT = process.env.PORT || 7000;

app.listen(PORT, () => {
    console.log(`Creamio addon running at: http://localhost:${PORT}`);
    console.log(`Manifest URL: http://localhost:${PORT}/manifest.json`);
});
