// server.js
const express = require('express');
const path = require('path');
const { addonBuilder } = require('stremio-addon-sdk');
const manifest = require('./manifest');
const { handleCatalog, handleMeta, handleStream } = require('./src/stream-handler');

console.log('🚀 Starting Creamio server...');

// Initialize the addon builder with the manifest
const builder = new addonBuilder(manifest);

// Define handlers for the addon's resources
builder.defineCatalogHandler(handleCatalog);
builder.defineMetaHandler(handleMeta);
builder.defineStreamHandler(handleStream);

console.log('✅ Addon builder initialized with handlers');

// --- Express App Setup ---
const app = express();

// Request logging middleware (FIRST)
app.use((req, res, next) => {
    console.log(`📥 [${new Date().toISOString()}] ${req.method} ${req.url}`);
    console.log(`📝 Headers:`, JSON.stringify(req.headers, null, 2));
    next();
});

// Add CORS middleware
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', '*');
    console.log('🌐 CORS headers set');
    next();
});

// Serve the static landing page and other files from the 'public' directory
app.use('/public', express.static(path.join(__dirname, 'public')));

// Redirect root to the landing page
app.get('/', (req, res) => {
    console.log('🏠 Root request - redirecting to /public/index.html');
    res.redirect('/public/index.html');
});

// Manually define Stremio addon routes with detailed logging
app.get('/manifest.json', (req, res) => {
    console.log('📋 Manifest requested');
    console.log('📋 Manifest content:', JSON.stringify(manifest, null, 2));
    res.json(manifest);
});

app.get('/catalog/:type/:id/:extra?.json', async (req, res) => {
    console.log('📚 CATALOG REQUEST RECEIVED');
    console.log('🔍 Type:', req.params.type);
    console.log('🔍 ID:', req.params.id);
    console.log('🔍 Extra (raw):', req.params.extra);
    
    try {
        let extraQuery = {};
        if (req.params.extra) {
            console.log('🔓 Decoding extra parameter...');
            const decodedExtra = decodeURIComponent(req.params.extra);
            console.log('🔓 Decoded extra:', decodedExtra);
            extraQuery = JSON.parse(decodedExtra);
            console.log('🔓 Parsed extra:', JSON.stringify(extraQuery, null, 2));
        }
        
        console.log('🎯 Calling handleCatalog with args:', {
            type: req.params.type,
            id: req.params.id,
            extra: extraQuery
        });
        
        const result = await handleCatalog({
            type: req.params.type,
            id: req.params.id,
            extra: extraQuery
        });
        
        console.log('✅ Catalog result:', JSON.stringify(result, null, 2));
        res.json(result);
        
    } catch (err) {
        console.error('❌ CATALOG ERROR:', err.message);
        console.error('❌ CATALOG STACK:', err.stack);
        res.status(500).json({ error: err.message, stack: err.stack });
    }
});

app.get('/meta/:type/:id.json', async (req, res) => {
    console.log('📖 META REQUEST RECEIVED');
    console.log('🔍 Type:', req.params.type);
    console.log('🔍 ID:', req.params.id);
    
    try {
        const result = await handleMeta({
            type: req.params.type,
            id: req.params.id
        });
        
        console.log('✅ Meta result:', JSON.stringify(result, null, 2));
        res.json(result);
        
    } catch (err) {
        console.error('❌ META ERROR:', err.message);
        console.error('❌ META STACK:', err.stack);
        res.status(500).json({ error: err.message, stack: err.stack });
    }
});

app.get('/stream/:type/:id.json', async (req, res) => {
    console.log('🎬 STREAM REQUEST RECEIVED');
    console.log('🔍 Type:', req.params.type);
    console.log('🔍 ID:', req.params.id);
    
    try {
        const result = await handleStream({
            type: req.params.type,
            id: req.params.id
        });
        
        console.log('✅ Stream result:', JSON.stringify(result, null, 2));
        res.json(result);
        
    } catch (err) {
        console.error('❌ STREAM ERROR:', err.message);
        console.error('❌ STREAM STACK:', err.stack);
        res.status(500).json({ error: err.message, stack: err.stack });
    }
});

// Catch-all route for debugging
app.use('*', (req, res) => {
    console.log('🔍 UNMATCHED ROUTE:', req.method, req.originalUrl);
    console.log('🔍 All params:', req.params);
    console.log('🔍 Query:', req.query);
    res.status(404).json({ 
        error: 'Route not found', 
        method: req.method, 
        url: req.originalUrl,
        availableRoutes: [
            'GET /',
            'GET /manifest.json', 
            'GET /catalog/:type/:id/:extra?.json',
            'GET /meta/:type/:id.json',
            'GET /stream/:type/:id.json'
        ]
    });
});

const PORT = process.env.PORT || 7000;
app.listen(PORT, () => {
    console.log('🎉 Creamio addon successfully started!');
    console.log(`🔗 Server running on port: ${PORT}`);
    console.log(`📦 Installation link: http://127.0.0.1:${PORT}`);
    console.log(`📋 Manifest URL: http://127.0.0.1:${PORT}/manifest.json`);
    
    // Test the manifest on startup
    console.log('🧪 Testing manifest...');
    console.log('📋 Manifest ID:', manifest.id);
    console.log('📋 Manifest catalogs:', manifest.catalogs);
});
