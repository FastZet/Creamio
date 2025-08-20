// server.js

const express = require('express');
const path = require('path');
const { handleCatalog, handleMeta, handleStream } = require('./src/stream-handler');
const manifest = require('./manifest');

const app = express();
const PORT = process.env.PORT || 7000;

// CORS Middleware
app.use((req, res, next) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Headers', '*');
    res.setHeader('Content-Type', 'application/json');
    next();
});

// Serve static landing page
app.use(express.static(path.join(__dirname, 'public')));
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Stremio Addon Routes
app.get('/manifest.json', (req, res) => {
    res.send(manifest);
});

app.get('/catalog/:type/:id/:extra?.json', async (req, res) => {
    try {
        const result = await handleCatalog(req.params);
        res.send(result);
    } catch (error) {
        console.error(error);
        res.status(500).send({ error: 'An internal error occurred.' });
    }
});

app.get('/meta/:type/:id.json', async (req, res) => {
    try {
        const result = await handleMeta(req.params);
        res.send(result);
    } catch (error) {
        console.error(error);
        res.status(500).send({ error: 'An internal error occurred.' });
    }
});

app.get('/stream/:type/:id.json', async (req, res) => {
    try {
        const result = await handleStream(req.params);
        res.send(result);
    } catch (error) {
        console.error(error);
        res.status(500).send({ error: 'An internal error occurred.' });
    }
});

// Start Server
app.listen(PORT, () => {
    console.log(`Creamio addon running at: http://localhost:${PORT}`);
});
