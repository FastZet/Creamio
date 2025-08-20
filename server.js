// server.js

const { addonBuilder, serveHTTP } = require('stremio-addon-sdk');
const manifest = require('./manifest');
const { handleCatalog, handleMeta, handleStream } = require('./src/stream-handler');

// Initialize the addon builder with the manifest
const builder = new addonBuilder(manifest);

// Define handlers for the addon's resources
builder.defineCatalogHandler(handleCatalog);
builder.defineMetaHandler(handleMeta);
builder.defineStreamHandler(handleStream);

const PORT = process.env.PORT || 7000;

// Use the SDK's serveHTTP function. This creates the server, sets up
// all the necessary routes for the addon, and can also serve static files.
serveHTTP(builder.getInterface(), { port: PORT, static: '/public' })
    .then(({ app }) => {
        // The `app` is an express instance, so we can add a root redirect
        // to the landing page for a better user experience.
        app.get('/', (req, res) => {
            res.redirect('/public/index.html');
        });
        
        console.log(`Creamio addon is running on port: ${PORT}`);
        console.log(`To install, visit: http://localhost:${PORT}`);
    })
    .catch(err => {
        console.error("Failed to start addon server:", err);
    });
