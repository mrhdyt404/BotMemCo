document.addEventListener("DOMContentLoaded", () => {
    fetchBTCStatus();
    fetchMarketEvents();
    fetchTrendingPredictions();
    fetchLiveFeed();
    fetchMLStatus();
    fetchDexScreenerMarquee();
    fetchWishlist();

    document.getElementById("refresh-btn").addEventListener("click", () => {
        fetchBTCStatus();
        fetchMarketEvents();
        fetchTrendingPredictions();
        fetchLiveFeed();
        fetchMLStatus();
        fetchDexScreenerMarquee();
    });

    document.getElementById("btn-refresh-wishlist").addEventListener("click", () => {
        fetchWishlist();
        fetchMLStatus();
    });

    document.getElementById("search-btn").addEventListener("click", performSearch);
    document.getElementById("token-input").addEventListener("keypress", (e) => {
        if (e.key === "Enter") performSearch();
    });

    // View Navigation Tabs
    const tabDashboard = document.getElementById("btn-tab-dashboard");
    const tabWishlist = document.getElementById("btn-tab-wishlist");
    const viewDashboard = document.getElementById("view-dashboard-page");
    const viewWishlist = document.getElementById("view-wishlist-page");

    tabDashboard.addEventListener("click", () => {
        tabDashboard.classList.add("active");
        tabWishlist.classList.remove("active");
        viewDashboard.classList.remove("hidden");
        viewWishlist.classList.add("hidden");
    });

    tabWishlist.addEventListener("click", () => {
        tabWishlist.classList.add("active");
        tabDashboard.classList.remove("active");
        viewWishlist.classList.remove("hidden");
        viewDashboard.classList.add("hidden");
        fetchWishlist();
    });

    // Auto refresh every 25 seconds
    setInterval(() => {
        fetchBTCStatus();
        fetchMarketEvents();
        fetchTrendingPredictions();
        fetchLiveFeed();
        fetchMLStatus();
        fetchDexScreenerMarquee();
    }, 25000);
});

async function fetchTrendingPredictions() {
    const tbody = document.getElementById("prediction-tbody");
    try {
        const res = await fetch("/api/trending");
        const data = await res.json();

        if (data.status === "ok" && data.predictions) {
            tbody.innerHTML = "";
            
            if (data.predictions.length > 0) {
                document.getElementById("top-coin-name").innerText = `$${data.predictions[0].token_symbol} (${data.predictions[0].pump_score}%)`;
            }

            const top3Data = data.top_recommendations || data.top_3_recommendations;
            if (top3Data) {
                renderRecommendations(top3Data);
            }

            data.predictions.forEach((pred, index) => {
                const tr = document.createElement("tr");

                let badgeClass = "badge-neutral";
                if (pred.recommendation.includes("STRONG BUY")) badgeClass = "badge-strong-buy";
                else if (pred.recommendation.includes("BULLISH")) badgeClass = "badge-bullish";
                else if (pred.recommendation.includes("BEARISH")) badgeClass = "badge-bearish";

                const velSign = pred.volume_velocity >= 0 ? "+" : "";

                // Robust property fallback extraction
                let tfText = pred.timeframe;
                let targetGainText = pred.target_gain;
                if (!tfText && pred.historical_pattern) {
                    tfText = pred.historical_pattern.timeframe_50 || pred.historical_pattern.badge_label || "1 - 3 Hari Ke Depan";
                }
                if (!targetGainText && pred.historical_pattern) {
                    targetGainText = pred.historical_pattern.expected_gain || "+50% s/d +100%+";
                }
                const ketAwam = pred.keterangan_awam || pred.layman_summary || "Perbincangan sosial stabil";
                const priceStr = pred.price_usd || "$0.000045";
                const change24h = pred.change_24h || 0;
                const isUp = change24h >= 0;

                tr.innerHTML = `
                    <td data-label="Rank">#${index + 1}</td>
                    <td data-label="Coin" class="coin-cell">$${pred.token_symbol}</td>
                    <td data-label="Jaringan"><span class="net-badge ${pred.network_class || 'net-eth'}">${pred.network_badge || '🔹 Ethereum'}</span></td>
                    <td data-label="Realtime Price">
                        <div class="timeframe-cell">
                            <strong>${priceStr}</strong><br>
                            <small class="price-change-badge ${isUp ? 'up' : 'down'}">${isUp ? '+' : ''}${change24h}%</small>
                        </div>
                    </td>
                    <td data-label="Pump Prob">
                        <div class="pump-bar-container">
                            <div class="pump-bar-bg">
                                <div class="pump-bar-fill" style="width: ${pred.pump_score}%"></div>
                            </div>
                            <span class="pump-text">${pred.pump_score}%</span>
                        </div>
                    </td>
                    <td data-label="Recommendation"><span class="badge ${badgeClass}">${pred.recommendation}</span></td>
                    <td data-label="Estimasi Waktu & Target">
                        <div class="timeframe-cell" style="color: var(--accent-cyan)">
                            ⏱️ ${tfText || '1 - 3 Hari Ke Depan'}<br>
                            <small style="color:var(--accent-green); font-weight:700;">${targetGainText || '+50% s/d +100%'}</small>
                        </div>
                    </td>
                    <td data-label="Keterangan (Ringkasan Awam)">
                        <div class="keterangan-cell">${ketAwam}</div>
                    </td>
                    <td data-label="1h Vol">${pred.post_count_1h}</td>
                    <td data-label="24h Vol">${pred.post_count_24h}</td>
                    <td data-label="Action">
                        <button class="btn-wishlist-add btn-wishlist-row" onclick="addCoinToWishlist('${pred.token_symbol}', '${priceStr}', ${pred.pump_score}, '${pred.recommendation}', '${targetGainText}', '${tfText}', '${ketAwam.replace(/'/g, "\\'")}')">
                            ⭐ Wishlist
                        </button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (e) {
        console.error("Error fetching predictions:", e);
    }
}

function renderRecommendations(top3) {
    const container = document.getElementById("recommendations-container");
    if (!container || !top3 || top3.length === 0) return;

    container.innerHTML = "";
    top3.forEach((coin, idx) => {
        const card = document.createElement("div");
        card.className = `rec-card rec-rank-${idx + 1}`;

        let tf = coin.timeframe || (coin.historical_pattern ? coin.historical_pattern.timeframe_50 : "Beberapa Jam / Hari Ke Depan");
        let gain = coin.target_gain || coin.expected_gain || "+50%+ Potensi Kenaikan";
        let desc = coin.keterangan_awam || coin.layman_summary || "Perbincangan sosial melonjak drastis";
        let priceStr = coin.price_usd || "$0.000045";
        let change24h = coin.change_24h || 12.5;
        let isUp = change24h >= 0;

        let timeframeTagClass = "tag-days";
        if (coin.timeframe_cat === "HOURS" || (coin.badge_label && coin.badge_label.includes("Jam"))) timeframeTagClass = "tag-hours";
        else if (coin.timeframe_cat === "WEEKS" || (coin.badge_label && coin.badge_label.includes("Minggu"))) timeframeTagClass = "tag-weeks";

        card.innerHTML = `
            <div>
                <div class="rec-header">
                    <div>
                        <span style="font-size:0.75rem; font-weight:800; color:var(--text-muted); letter-spacing:0.5px;">REKOMENDASI DIBELI #${idx + 1}</span>
                        <div class="rec-coin-name">$${coin.token_symbol} <span class="net-badge ${coin.network_class || 'net-eth'}" style="margin-left:6px; font-size:0.7rem; font-weight:700;">${coin.network_badge || '🔹 Ethereum'}</span></div>
                        <div class="rec-price-box">
                            <span class="realtime-price">${priceStr}</span>
                            <span class="price-change-badge ${isUp ? 'up' : 'down'}">${isUp ? '+' : ''}${change24h}%</span>
                        </div>
                    </div>
                    <span class="rec-timeframe-tag ${timeframeTagClass}">⏱️ ${tf}</span>
                </div>
                <div class="rec-gain-box">
                    <span class="rec-gain-label">Target Kenaikan</span>
                    <span class="rec-gain-val">${gain}</span>
                </div>
                <p class="rec-desc">💡 ${desc}</p>
            </div>
            <div>
                <div style="margin-top:14px; padding-top:10px; border-top:1px dashed rgba(255,255,255,0.1); font-size:0.8rem; color:var(--text-muted); display:flex; justify-content:space-between; align-items:center;">
                    <span>Skor ML: <strong style="color:var(--accent-cyan); font-family:var(--font-mono);">${coin.pump_score}%</strong></span>
                    <span class="badge ${coin.recommendation.includes('STRONG BUY') ? 'badge-strong-buy' : coin.recommendation.includes('BULLISH') ? 'badge-bullish' : 'badge-neutral'}">${coin.recommendation}</span>
                </div>
                <button class="btn-wishlist-add" onclick="addCoinToWishlist('${coin.token_symbol}', '${priceStr}', ${coin.pump_score}, '${coin.recommendation}', '${gain}', '${tf}', '${desc.replace(/'/g, "\\'")}')">
                    ⭐ + Tambah ke Wishlist & Tracker
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

// Wishlist Functionality
async function addCoinToWishlist(tokenSymbol, priceStr, pumpScore, recommendation, targetGain, timeframe, keteranganAwam) {
    try {
        const res = await fetch("/api/wishlist/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                token_symbol: tokenSymbol,
                entry_price_str: priceStr,
                pump_score: pumpScore,
                recommendation: recommendation,
                target_gain: targetGain,
                timeframe: timeframe,
                keterangan_awam: keteranganAwam
            })
        });
        const data = await res.json();
        if (data.status === "ok") {
            alert(`⭐ Koin $${tokenSymbol} (${priceStr}) berhasil ditambahkan ke Wishlist & Tracker!\n\nSistem akan memantau fluktuasi harga dalam ${timeframe} untuk menguji keakuratan prediksi dan melatih model ML.`);
            fetchWishlist();
        }
    } catch (e) {
        console.error("Error adding to wishlist:", e);
        alert("Gagal menambahkan ke Wishlist.");
    }
}

async function fetchWishlist() {
    const container = document.getElementById("wishlist-container");
    const badge = document.getElementById("wishlist-badge");
    try {
        const res = await fetch("/api/wishlist");
        const data = await res.json();

        if (data.status === "ok" && data.wishlist) {
            badge.innerText = data.wishlist.length;
            
            if (data.wishlist.length === 0) {
                container.innerHTML = `
                    <div class="wishlist-empty-state">
                        <p>Belum ada koin di Wishlist. Klik tombol <strong>⭐ + Wishlist</strong> pada kartu rekomendasi teratas untuk mulai melacak!</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = "";
            data.wishlist.forEach(item => {
                const card = document.createElement("div");
                const isSuccess = item.status.includes("BENAR") || item.status.includes("🎯");
                card.className = `wishlist-card ${isSuccess ? 'status-success' : ''}`;

                const gainSign = item.current_gain_pct >= 0 ? "+" : "";
                const isUp = item.current_gain_pct >= 0;

                card.innerHTML = `
                    <div>
                        <div class="wishlist-card-header">
                            <div>
                                <span style="font-size:0.7rem; font-weight:800; color:var(--text-muted);">TRACKING WISHLIST #${item.id}</span>
                                <div class="wishlist-token-title">$${item.token_symbol} <span class="net-badge ${item.network_class || 'net-eth'}" style="font-size:0.7rem; margin-left:6px;">${item.network_badge || '🔹 Ethereum'}</span></div>
                            </div>
                            <span class="wishlist-status-badge ${isSuccess ? 'status-badge-success' : 'status-badge-tracking'}">
                                ${item.status}
                            </span>
                        </div>

                        <div class="wishlist-price-comparison">
                            <div class="price-box-item">
                                <span class="price-box-label">Harga Saat Wishlist</span>
                                <span class="price-box-value">${item.entry_price_str}</span>
                            </div>
                            <div style="font-size:1.2rem; color:var(--text-muted);">➔</div>
                            <div class="price-box-item" style="text-align:right;">
                                <span class="price-box-label">Harga Market Live</span>
                                <span class="price-box-value" style="color: ${isUp ? 'var(--accent-green)' : 'var(--accent-pink)'}">
                                    ${item.current_price_str} (${gainSign}${item.current_gain_pct}%)
                                </span>
                            </div>
                        </div>

                        <div style="background:rgba(0,0,0,0.2); padding:10px; border-radius:8px; margin-bottom:10px; font-size:0.8rem; line-height:1.4;">
                            • <strong>Target Kenaikan:</strong> <span style="color:var(--accent-green); font-weight:700;">${item.target_gain}</span><br>
                            • <strong>Estimasi Waktu:</strong> <span style="color:var(--accent-cyan); font-weight:700;">⏱️ ${item.timeframe}</span><br>
                            • <strong>Skor ML:</strong> ${item.pump_score}% (${item.recommendation})<br>
                            • <strong>Keterangan:</strong> <em>${item.keterangan_awam}</em>
                        </div>

                        ${item.fed_to_ml === 1 ? `
                            <div style="background:rgba(0,230,118,0.15); border:1px solid var(--accent-green); padding:6px 10px; border-radius:6px; font-size:0.75rem; color:var(--accent-green); font-weight:700; margin-bottom:10px;">
                                🧠 Hasil Prediksi Berhasil Dipelajari oleh Continuous ML Engine!
                            </div>
                        ` : ''}
                    </div>

                    <div>
                        ${!isSuccess ? `
                            <button class="btn-simulate-pump" onclick="simulateWishlistPump(${item.id})">
                                🧪 Uji Demo Simulasi Kenaikan (+50%+) & Latih ML
                            </button>
                        ` : ''}
                        <button class="btn-delete-wishlist" onclick="deleteWishlist(${item.id})">
                            🗑️ Hapus dari Wishlist
                        </button>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Error fetching wishlist:", e);
    }
}

async function simulateWishlistPump(wishlistId) {
    try {
        const res = await fetch(`/api/wishlist/simulate_pump/${wishlistId}`, { method: "POST" });
        const data = await res.json();
        if (data.status === "ok") {
            alert(data.message);
            fetchWishlist();
            fetchMLStatus();
        }
    } catch (e) {
        console.error("Error simulating pump:", e);
    }
}

async function deleteWishlist(wishlistId) {
    try {
        await fetch(`/api/wishlist/${wishlistId}`, { method: "DELETE" });
        fetchWishlist();
    } catch (e) {
        console.error("Error deleting wishlist:", e);
    }
}

async function fetchLiveFeed() {
    const feedContainer = document.getElementById("post-feed");
    try {
        const res = await fetch("/api/feed?limit=25");
        const data = await res.json();

        if (data.status === "ok" && data.posts && data.posts.length > 0) {
            feedContainer.innerHTML = "";
            data.posts.forEach(post => {
                const item = document.createElement("div");
                item.className = "feed-item";

                const sentColor = post.sentiment_score >= 0.1 ? "var(--accent-green)" : post.sentiment_score <= -0.1 ? "var(--accent-pink)" : "var(--accent-gold)";

                item.innerHTML = `
                    <div class="feed-meta">
                        <span><strong class="platform-tag ${post.platform}">${post.platform}</strong> ${post.author}</span>
                        <span style="color: ${sentColor}">Score: ${post.sentiment_score > 0 ? '+' : ''}${post.sentiment_score.toFixed(2)}</span>
                    </div>
                    <div class="feed-content">${post.content}</div>
                `;
                feedContainer.appendChild(item);
            });
        }
    } catch (e) {
        console.error("Error fetching feed:", e);
    }
}

async function fetchMLStatus() {
    try {
        const res = await fetch("/api/ml/status");
        const data = await res.json();

        if (data.status === "ok") {
            document.getElementById("ml-sample-count").innerText = data.samples_trained;
            
            const logList = document.getElementById("ml-log-list");
            if (data.logs && data.logs.length > 0) {
                logList.innerHTML = "";
                data.logs.forEach(log => {
                    const li = document.createElement("li");
                    li.innerText = `[${log.timestamp.split(' ')[1] || log.timestamp}] ${log.version} | Acc: ${log.accuracy}% | ${log.notes}`;
                    logList.appendChild(li);
                });
            }
        }
    } catch (e) {
        console.error("Error fetching ML status:", e);
    }
}

async function performSearch() {
    const input = document.getElementById("token-input").value.trim().toUpperCase();
    const resultBox = document.getElementById("search-result");
    if (!input) return;

    resultBox.classList.remove("hidden");
    resultBox.innerHTML = "Computing features & ML prediction...";

    try {
        const res = await fetch(`/api/predict/${input}`);
        const data = await res.json();

        resultBox.innerHTML = `
            <strong>$${data.token_symbol} ML Prediction:</strong> <span class="net-badge ${data.network_class || 'net-eth'}" style="font-size:0.7rem; margin-left:6px;">${data.network_badge || '🔹 Ethereum'}</span><br>
            • Realtime Price: <strong style="color:var(--text-main)">${data.price_usd}</strong> (${data.change_24h}%)<br>
            • Pump Score: <strong style="color:var(--accent-cyan)">${data.pump_score}%</strong> (${data.recommendation})<br>
            • Target Gain: <strong style="color:var(--accent-green)">${data.target_gain}</strong><br>
            • Waktu Kenaikan: <strong>${data.timeframe}</strong><br>
            • Keterangan: <em>${data.keterangan_awam}</em><br>
            • 1h Posts: ${data.features.post_count_1h} | Velocity: ${(data.features.volume_velocity * 100).toFixed(0)}%
        `;
    } catch (e) {
        resultBox.innerHTML = `Error checking token ${input}`;
    }
}

async function fetchDexScreenerMarquee() {
    const container = document.getElementById("marquee-content");
    try {
        const res = await fetch("/api/dexscreener");
        const data = await res.json();

        if (data.status === "ok" && data.tickers && data.tickers.length > 0) {
            const renderItems = (items) => items.map(t => {
                const isUp = t.change_24h >= 0;
                const changeSign = isUp ? "+" : "";
                const changeClass = isUp ? "up" : "down";
                return `
                    <span class="marquee-item">
                        <span class="marquee-symbol">$${t.symbol}</span>
                        <span class="net-badge ${t.network_class || 'net-eth'}" style="font-size:0.65rem; padding:2px 6px; margin:0 4px;">${t.network_badge || '🔹 ETH'}</span>
                        <span class="marquee-price">${t.price}</span>
                        <span class="marquee-change ${changeClass}">${changeSign}${t.change_24h}%</span>
                        <span style="opacity:0.3">|</span>
                    </span>
                `;
            }).join("");

            container.innerHTML = renderItems(data.tickers) + renderItems(data.tickers);
        }
    } catch (e) {
        console.error("Error fetching DEX Screener marquee:", e);
    }
}

async function fetchBTCStatus() {
    try {
        const res = await fetch("/api/btc");
        const data = await res.json();
        if (data.status === "ok" && data.btc) {
            const btc = data.btc;
            document.getElementById("btc-price-usd").innerText = btc.price_usd;
            
            const changeBadge = document.getElementById("btc-change-24h");
            const isUp = btc.change_24h >= 0;
            changeBadge.innerText = `${isUp ? '+' : ''}${btc.change_24h}%`;
            changeBadge.className = `price-change-badge ${isUp ? 'up' : 'down'}`;
            
            document.getElementById("btc-sentiment").innerText = btc.market_sentiment;
            document.getElementById("btc-macro-summary").innerText = btc.macro_health_summary;
        }
    } catch (e) {
        console.error("Error fetching BTC status:", e);
    }
}

async function fetchMarketEvents() {
    const container = document.getElementById("market-events-container");
    if (!container) return;

    try {
        const res = await fetch("/api/events");
        const data = await res.json();

        if (data.status === "ok" && data.events && data.events.length > 0) {
            container.innerHTML = "";
            data.events.forEach(evt => {
                const card = document.createElement("div");
                card.className = `event-card ${evt.direction_class}`;

                const targetCoinsHtml = evt.target_coins.map(c => `<span class="net-badge net-eth" style="font-size:0.65rem; padding:1px 6px;">$${c}</span>`).join(" ");

                const newsLinkHtml = evt.source_url ? `
                    <a href="${evt.source_url}" target="_blank" rel="noopener noreferrer" class="news-source-badge" title="Buka berita di ${evt.source_name || 'Situs Berita'} (${evt.source_domain || ''})">
                        ${evt.source_badge || '🌐 ' + (evt.source_name || 'Sumber Berita')} ↗
                    </a>
                ` : '';

                const sourceRowHtml = evt.source_url ? `
                    <div class="evt-source-row">
                        <span style="color:var(--text-muted);">📰 Sumber Berita:</span>
                        <a href="${evt.source_url}" target="_blank" rel="noopener noreferrer" class="evt-source-link">
                            ${evt.source_name} <span style="font-size:0.7rem; color:var(--text-muted);">(${evt.source_domain})</span> ↗
                        </a>
                    </div>
                ` : '';

                card.innerHTML = `
                    <div>
                        <div class="evt-header">
                            <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                                <span class="net-badge net-doge" style="font-size:0.65rem;">📌 ${evt.category}</span>
                                ${newsLinkHtml}
                            </div>
                            <span class="evt-time">⏱️ ${evt.timestamp}</span>
                        </div>
                        <div class="evt-title">${evt.title}</div>
                        <div class="evt-summary">${evt.summary}</div>
                        ${sourceRowHtml}
                    </div>
                    <div>
                        <div style="margin-bottom:8px; font-size:0.78rem;">
                            <strong>Koin Terdampak:</strong> ${targetCoinsHtml} | Dampak: <strong style="color:var(--accent-cyan);">${evt.impact_rating}</strong>
                        </div>
                        <div class="hist-match-box">
                            <div class="hist-match-title">
                                <span>📜 Pencocokan Histori Berita</span>
                                <span style="color:var(--accent-green); font-weight:800;">🎯 ${evt.historical_match.similarity_score}% Kemiripan</span>
                            </div>
                            • <strong>Peristiwa Histori Lalu:</strong> <em>${evt.historical_match.matched_event}</em><br>
                            • <strong>Hasil Kenaikan/Koreksi Histori:</strong> <span style="color:var(--accent-green); font-weight:700;">${evt.historical_match.historical_result}</span><br>
                            • <strong>Sinyal Pembelajaran ML:</strong> <code style="color:var(--accent-cyan);">${evt.historical_match.ml_signal}</code>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            });
        }
    } catch (e) {
        console.error("Error fetching market events:", e);
    }
}

