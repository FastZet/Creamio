// src/scrapers/pornmd.js
const axios = require('axios');
const config = require('../config');

function buildUrl(query) {
    const encodedQuery = encodeURIComponent(query.trim());
    return config.scrapers.find(s => s.id === 'pornmd').searchUrl.replace('{{query}}', encodedQuery);
}

async function scrapePornmd(query) {
    const url = buildUrl(query);
    console.log('🔗 PornMD URL:', url);
    
    const { userAgent, timeout } = config.client;

    try {
        const response = await axios.get(url, {
            headers: { 'User-Agent': userAgent },
            timeout: timeout
        });
        
        console.log('📄 PornMD response status:', response.status);
        console.log('📝 PornMD response length:', response.data.length);
        
        const html = response.data;
        
        // Check for blocks
        if (html.includes('Cloudflare') || html.includes('Access denied') || html.includes('Just a moment')) {
            console.error('❌ PornMD blocked by protection service');
            return { error: 'Blocked by protection service', reason: 'Detected protection service' };
        }
        
        const videos = [];
        
        // Same manual parsing patterns as Metaporn
        const linkRegex = /<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<img[^>]+src="([^"]+)"[^>]*alt="([^"]*)"[\s\S]*?<\/a>/gi;
        let match;
        
        while ((match = linkRegex.exec(html)) !== null && videos.length < 20) {
            const [, href, imgSrc, altText] = match;
            
            if (href && imgSrc && (href.includes('/video/') || href.includes('/watch/') || href.includes('.html'))) {
                let videoUrl = href.startsWith('http') ? href : `${config.scrapers.find(s => s.id === 'pornmd').baseUrl}${href}`;
                let title = altText || 'Unknown Video';
                let thumbnail = imgSrc.startsWith('http') ? imgSrc : `${config.scrapers.find(s => s.id === 'pornmd').baseUrl}${imgSrc}`;
                
                const contextStart = Math.max(0, match.index - 500);
                const contextEnd = Math.min(html.length, match.index + match[0].length + 500);
                const context = html.slice(contextStart, contextEnd);
                
                const durationMatch = context.match(/(\d{1,2}:\d{2}(?::\d{2})?)/);
                const duration = durationMatch ? durationMatch[1] : 'N/A';
                
                videos.push({
                    title: title.substring(0, 100).trim(),
                    url: videoUrl,
                    thumbnail: thumbnail,
                    duration: duration,
                    source: 'PornMD'
                });
            }
        }
        
        // Alternative patterns (same as Metaporn)
        if (videos.length === 0) {
            const titleRegex = /<a[^>]+href="([^"]+)"[^>]+title="([^"]+)"[^>]*>[\s\S]*?<\/a>/gi;
            
            while ((match = titleRegex.exec(html)) !== null && videos.length < 20) {
                const [, href, title] = match;
                
                if (href && title && (href.includes('/video/') || href.includes('/watch/') || href.includes('.html'))) {
                    let videoUrl = href.startsWith('http') ? href : `${config.scrapers.find(s => s.id === 'pornmd').baseUrl}${href}`;
                    
                    const contextStart = Math.max(0, match.index - 300);
                    const contextEnd = Math.min(html.length, match.index + match[0].length + 300);
                    const context = html.slice(contextStart, contextEnd);
                    
                    const imgMatch = context.match(/<img[^>]+src="([^"]+)"/i);
                    const thumbnail = imgMatch ? (imgMatch[1].startsWith('http') ? imgMatch[1] : `${config.scrapers.find(s => s.id === 'pornmd').baseUrl}${imgMatch[1]}`) : '';
                    
                    const durationMatch = context.match(/(\d{1,2}:\d{2}(?::\d{2})?)/);
                    const duration = durationMatch ? durationMatch[1] : 'N/A';
                    
                    videos.push({
                        title: title.substring(0, 100).trim(),
                        url: videoUrl,
                        thumbnail: thumbnail,
                        duration: duration,
                        source: 'PornMD'
                    });
                }
            }
        }
        
        if (videos.length === 0) {
            console.log('🔍 PornMD HTML sample (first 1000 chars):', html.substring(0, 1000));
            return { 
                error: 'No results found', 
                reason: 'No video links found in HTML. The site structure may have changed or search returned no results.'
            };
        }
        
        const uniqueVideos = videos.filter((video, index, self) => 
            self.findIndex(v => v.url === video.url) === index
        );
        
        console.log(`🎉 PornMD scraped ${uniqueVideos.length} unique videos successfully`);
        return uniqueVideos.slice(0, 15);
        
    } catch (error) {
        console.error(`❌ PornMD error for "${query}":`, error.message);
        return { 
            error: 'Connection failed', 
            reason: `Could not connect to PornMD: ${error.message}` 
        };
    }
}

module.exports = { scrapePornmd };
