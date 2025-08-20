# Creamio 🍦 - Stremio Addon

Creamio is a dynamic, search-driven Stremio addon that generates content catalogs by scraping popular adult search engines. It acts as a bridge, transforming your search queries into browsable, series-like catalogs within Stremio, with all video playback handled externally for privacy and simplicity.

## ✨ Features

*   **Dynamic Search-Based Catalogs**: Instead of static catalogs, Creamio creates them on-the-fly based on your search query. Each supported website appears as its own catalog in the search results.
*   **Modular Scraper Engine**: Each scraped website is handled by its own dedicated module, making it easy to maintain, update, or add new sources without affecting others.
*   **Rich Metadata**: Where available, the addon scrapes video titles, thumbnails, and durations, presenting search results in a familiar, user-friendly "episode list" format inside Stremio.
*   **Intelligent Failure Handling**: If a specific site's scraper fails (due to layout changes, anti-bot measures like Cloudflare, or downtime), the addon will clearly report the issue directly within the Stremio UI instead of just showing an empty folder.
*   **Performance-First Caching**: Search results are cached for **one week**. This provides instantaneous results for repeated searches and dramatically reduces the number of requests sent to the source websites.
*   **External & Private Playback**: All video links are opened in an external browser or application. No video data is ever proxied through the addon server.

## ⚙️ How It Works (User Flow)

The addon is designed to be intuitive and mimic the behavior of official Stremio addons.

1.  **Search**: The user enters a search query in the Stremio search bar (e.g., `"Leah Gotti in Kitchen"`).
2.  **Catalog of Sources**: Creamio intercepts the search and scrapes all configured websites in parallel. For each site that returns results, it generates a catalog item. The user sees a list like:
    *   `Results from Metaporn` (with Metaporn logo)
    *   `Results from PornMD` (with PornMD logo)
3.  **Selecting a Source**: The user clicks on one of the sources (e.g., `Results from Metaporn`).
4.  **Video List (Presented as a Series)**: The addon then performs a detailed scrape of the selected website for that specific query, fetching the top 20-30 video results. These are presented as a Stremio "series," where each video is an "episode." The user sees a list of videos with thumbnails, titles, and durations.
5.  **Playback**: The user clicks on a video from the list. The addon provides Stremio with a direct, external URL to that video's page. Stremio then opens this link in the user's default web browser or a relevant application.

## 🏗️ Architecture & Modularity

The addon is built with Node.js and Express, following a highly modular design to ensure long-term maintainability.

#### Core File Structure

```
.
└── creamio-addon/
    ├── server.js               # Express server setup, routing, and initialization.
    ├── manifest.js             # Defines the addon's properties for Stremio.
    ├── index.html              # Static landing page with the "Install" button.
    └── src/
        ├── config.js               # Stores URLs, CSS selectors, and other constants.
        ├── stream-handler.js       # The main controller that orchestrates all addon logic.
        ├── meta-builder.js         # Formats scraped data into Stremio-compatible meta objects.
        └── scrapers/
            ├── metaporn.js         # Scraper logic exclusively for Metaporn.
            ├── pornmd.js           # Scraper logic exclusively for PornMD.
            └── index.js            # Exports an array of all available scrapers.
```

This structure allows a developer to fix or add a scraper by only touching the relevant file in the `scrapers/` directory and its corresponding entry in `config.js`.

#### Error Handling Strategy

When a scraper fails, it will attempt to identify the cause and report it.

*   **HTML Structure Change**: If expected CSS selectors are not found, the error message will indicate a probable layout change.
*   **Anti-Bot / Cloudflare**: If the returned HTML contains signatures of bot protection (like a Cloudflare challenge page), the error will reflect this.
*   **General Failure**: For timeouts or other network issues, a generic "Failed to reach site" message will be shown.

This information will be presented in a disabled-style "video" item in Stremio, ensuring the user is always informed.

## ⚡ Caching Strategy

To ensure a fast user experience and to be a good internet citizen, Creamio employs a robust caching strategy:

*   **Catalog & Meta Responses**: All search results (both the initial list of sources and the detailed video lists) are cached for **one week**.
*   **Stale-While-Revalidate**: The caching mechanism can be configured to serve stale (cached) data while fetching fresh data in the background, though for a one-week TTL this is less critical.

## 🔌 API / Routes

The addon exposes the standard Stremio addon API endpoints:

*   `GET /manifest.json`: Provides the addon's manifest.
*   `GET /catalog/:type/:id/:extra?.json`: Handles search queries and returns the catalog of sources.
*   `GET /meta/:type/:id.json`: Fetches and formats the detailed list of videos for a selected source.
*   `GET /stream/:type/:id.json`: Provides the external stream URL for a selected video.

## 📜 Disclaimer

Creamio is purely a search engine. It does not host, upload, or stream any content. It functions by scraping publicly available information from third-party websites. The user is solely responsible for the content they choose to access and for complying with all applicable laws in their region. The developers of Creamio have no affiliation with the websites being scraped.

## 📄 License

This project is licensed under the MIT License.
