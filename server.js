// server.js

const { addonBuilder, serveHTTP } = require('stremio-addon-sdk');
const manifest = require('./manifest');
const { handleCatalog, handleMeta, handleStream } = require('./src/stream-handler');
const path = require('path');
const express = require('express');

// Create the addon builder instance
const builder = new addonBuilder(manifest);

// Register handlers for each resource
// The SDK automatically maps the IDs and types from the manifest
builder.defineCatalogHandler(handleCatalog);
builder.defineMetaHandler(handleMeta);
builder.defineStreamHandler(handleStream);

// Create an express app for the landing page
const app = express();
app.use(express.static(path.join(__dirname, 'public')));
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Use the SDK's serveHTTP method, which returns a request handler
// and mount it on the express app.
const addonInterface = builder.getInterface();
app.use((req, res, next) => {
    // Check if the request is for the addon's API
    if (req.url.startsWith(`/${manifest.id}`)) {
        addonInterface.middleware(req, res, next);
    } else {
        next();
    }
});

const PORT = process.env.PORT || 7000;

app.listen(PORT, () => {
    console.log(`Creamio addon running at: http://localhost:${PORT}`);
    console.log(`Stremio manifest URL: http://localhost:${PORT}/manifest.json`);
});
