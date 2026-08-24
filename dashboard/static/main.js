document.addEventListener("DOMContentLoaded", () => {
    fetchTrendingPredictions();
    fetchLiveFeed();
    fetchMLStatus();
    fetchDexScreenerMarquee();

    document.getElementById("refresh-btn").addEventListener("click", () => {
        fetchTrendingPredictions();
        fetchLiveFeed();
        fetchMLStatus();
        fetchDexScreenerMarquee();
    });

    document.getElementById("search-btn").addEventListener("click", performSearch);
    document.getElementById("token-input").addEventListener("keypress", (e) => {
        if (e.key === "Enter") performSearch();
    });

    // Auto refresh every 25 seconds
    setInterval(() => {
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

                tr.innerHTML = `
                    <td data-label="Rank">#${index + 1}</td>
                    <td data-label="Coin" class="coin-cell">$${pred.token_symbol}</td>
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
                    <td data-label="Vol Velocity" style="color: ${pred.volume_velocity >= 0 ? 'var(--accent-green)' : 'var(--accent-pink)'}">
                        ${velSign}${Math.round(pred.volume_velocity * 100)}%
                    </td>
                    <td data-label="Avg Sent">${pred.avg_sentiment > 0 ? '+' : ''}${pred.avg_sentiment.toFixed(2)}</td>
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

        let timeframeTagClass = "tag-days";
        if (coin.timeframe_cat === "HOURS" || (coin.badge_label && coin.badge_label.includes("Jam"))) timeframeTagClass = "tag-hours";
        else if (coin.timeframe_cat === "WEEKS" || (coin.badge_label && coin.badge_label.includes("Minggu"))) timeframeTagClass = "tag-weeks";

        card.innerHTML = `
            <div>
                <div class="rec-header">
                    <div>
                        <span style="font-size:0.75rem; font-weight:800; color:var(--text-muted); letter-spacing:0.5px;">REKOMENDASI DIBELI #${idx + 1}</span>
                        <div class="rec-coin-name">$${coin.token_symbol}</div>
                    </div>
                    <span class="rec-timeframe-tag ${timeframeTagClass}">⏱️ ${tf}</span>
                </div>
                <div class="rec-gain-box">
                    <span class="rec-gain-label">Target Kenaikan</span>
                    <span class="rec-gain-val">${gain}</span>
                </div>
                <p class="rec-desc">💡 ${desc}</p>
            </div>
            <div style="margin-top:14px; padding-top:10px; border-top:1px dashed rgba(255,255,255,0.1); font-size:0.8rem; color:var(--text-muted); display:flex; justify-content:space-between; align-items:center;">
                <span>Skor ML: <strong style="color:var(--accent-cyan); font-family:var(--font-mono);">${coin.pump_score}%</strong></span>
                <span class="badge ${coin.recommendation.includes('STRONG BUY') ? 'badge-strong-buy' : coin.recommendation.includes('BULLISH') ? 'badge-bullish' : 'badge-neutral'}">${coin.recommendation}</span>
            </div>
        `;
        container.appendChild(card);
    });
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
            <strong>$${data.token_symbol} ML Prediction:</strong><br>
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
            // Create items string twice for seamless loop
            const renderItems = (items) => items.map(t => {
                const isUp = t.change_24h >= 0;
                const changeSign = isUp ? "+" : "";
                const changeClass = isUp ? "up" : "down";
                return `
                    <span class="marquee-item">
                        <span class="marquee-symbol">$${t.symbol}</span>
                        <span class="marquee-price">${t.price}</span>
                        <span class="marquee-change ${changeClass}">${changeSign}${t.change_24h}%</span>
                        <span style="opacity:0.3">|</span>
                    </span>
                `;
            }).join("");

            // Duplicate array to ensure infinite CSS marquee loop
            container.innerHTML = renderItems(data.tickers) + renderItems(data.tickers);
        }
    } catch (e) {
        console.error("Error fetching DEX Screener marquee:", e);
    }
}
