// server.js
const express = require('express');
const path = require('path');
const { addonBuilder } = require('stremio-addon-sdk');
const manifest = require('./manifest');
const { handleCatalog, handleMeta, handleStream } = require('./src/stream-handler');

console.log('🚀 Starting Creamio server...');

const builder = new addonBuilder(manifest);
builder.defineCatalogHandler(handleCatalog);
builder.defineMetaHandler(handleMeta);
builder.defineStreamHandler(handleStream);

console.log('✅ Addon builder initialized with handlers');

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

app.use('/public', express.static(path.join(__dirname, 'public')));

app.get('/', (req, res) => {
    console.log('🏠 Root request - redirecting to /public/index.html');
    res.redirect('/public/index.html');
});

app.get('/manifest.json', (req, res) => {
    console.log('📋 Manifest requested');
    console.log('📋 Manifest content:', JSON.stringify(manifest, null, 2));
    res.json(manifest);
});

// ✅ FIXED CATALOG ROUTE
app.get('/catalog/:type/:id/:extra?.json', async (req, res) => {
    console.log('📚 CATALOG REQUEST RECEIVED');
    console.log('🔍 Type:', req.params.type);
    console.log('🔍 ID:', req.params.id);
    console.log('🔍 Extra (raw):', req.params.extra);
    
    try {
        let extraQuery = {};
        if (req.params.extra) {
            console.log('🔓 Parsing extra parameter...');
            const decodedExtra = decodeURIComponent(req.params.extra);
            console.log('🔓 Decoded extra:', decodedExtra);
            
            // Parse query string format (search=value&other=value2) instead of JSON
            if (decodedExtra.includes('=')) {
                // It's a query string format like "search=mia melano"
                const params = new URLSearchParams(decodedExtra);
                extraQuery = Object.fromEntries(params.entries());
                console.log('🔓 Parsed as query string:', JSON.stringify(extraQuery, null, 2));
            } else {
                // Try to parse as JSON (fallback)
                try {
                    extraQuery = JSON.parse(decodedExtra);
                    console.log('🔓 Parsed as JSON:', JSON.stringify(extraQuery, null, 2));
                } catch (jsonError) {
                    console.error('❌ Failed to parse as JSON or query string:', decodedExtra);
                    extraQuery = {};
                }
            }
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
    res.status(404).json({ 
        error: 'Route not found', 
        method: req.method, 
        url: req.originalUrl
    });
});

const PORT = process.env.PORT || 7000;
app.listen(PORT, () => {
    console.log('🎉 Creamio addon successfully started!');
    console.log(`🔗 Server running on port: ${PORT}`);
    console.log(`📋 Manifest URL: http://127.0.0.1:${PORT}/manifest.json`);
});
