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

// --- Express App Setup ---
const app = express();

// Add CORS middleware
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', '*');
    next();
});

// Serve the static landing page and other files from the 'public' directory
app.use('/public', express.static(path.join(__dirname, 'public')));

// Redirect root to the landing page
app.get('/', (req, res) => {
    res.redirect('/public/index.html');
});

// Manually define Stremio addon routes
app.get('/manifest.json', (req, res) => {
    res.json(manifest);
});

app.get('/catalog/:type/:id/:extra?.json', async (req, res) => {
    try {
        const extraQuery = req.params.extra ? JSON.parse(decodeURIComponent(req.params.extra)) : {};
        const result = await handleCatalog({
            type: req.params.type,
            id: req.params.id,
            extra: extraQuery
        });
        res.json(result);
    } catch (err) {
        console.error('Catalog error:', err);
        res.status(500).json({ error: err.message });
    }
});

app.get('/meta/:type/:id.json', async (req, res) => {
    try {
        const result = await handleMeta({
            type: req.params.type,
            id: req.params.id
        });
        res.json(result);
    } catch (err) {
        console.error('Meta error:', err);
        res.status(500).json({ error: err.message });
    }
});

app.get('/stream/:type/:id.json', async (req, res) => {
    try {
        const result = await handleStream({
            type: req.params.type,
            id: req.params.id
        });
        res.json(result);
    } catch (err) {
        console.error('Stream error:', err);
        res.status(500).json({ error: err.message });
    }
});

const PORT = process.env.PORT || 7000;
app.listen(PORT, () => {
    console.log(`Creamio addon running on port: ${PORT}`);
    console.log(`Installation link: http://127.0.0.1:${PORT}`);
});
