/**
 * SocialScope-Tweets Dashboard Visualization
 * Advanced interactive visualizations for Twitter analysis
 */

// Data storage for charts and tweet display
let dashboardData = {
    tweets: [],
    sentimentData: { positive: 0, neutral: 0, negative: 0 },
    tweetTypes: { regular: 0, replies: 0 },
    engagement: { likes: 0, retweets: 0, replies: 0 },
    topics: [],
    topicCounts: [],
    styleInsights: [],
    currentPage: 1,
    tweetsPerPage: 10
};

/**
 * Initialize the dashboard with data extracted from summary
 */
function initializeDashboard(summaryContentJson) {
    // Parse the JSON string (escaped from Jinja)
    const summaryContent = JSON.parse(summaryContentJson);
    
    // Extract data from summary text
    extractDashboardData(summaryContent);
    
    // Initialize all visualizations
    createSentimentChart();
    createTweetTypesChart();
    createEngagementChart(); 
    createTopicsChart();
    
    // Setup writing style indicators
    setupWritingStyleIndicators();
    
    // Setup tweet table with pagination
    setupTweetTable();
    
    // Extract and display highlights
    extractHighlights(summaryContent);
}

/**
 * Extract useful data from the summary text
 */
function extractDashboardData(summaryText) {
    // Extract sentiment percentages
    const sentimentMatch = summaryText.match(/Positive: ([\d.]+)%\s+Neutral: ([\d.]+)%\s+Negative: ([\d.]+)%/);
    if (sentimentMatch && sentimentMatch.length >= 4) {
        dashboardData.sentimentData.positive = parseFloat(sentimentMatch[1]);
        dashboardData.sentimentData.neutral = parseFloat(sentimentMatch[2]);
        dashboardData.sentimentData.negative = parseFloat(sentimentMatch[3]);
    }
    
    // Extract tweet type distribution
    const typeMatch = summaryText.match(/Regular tweets: ([\d.]+)%\s+Replies: ([\d.]+)%/);
    if (typeMatch && typeMatch.length >= 3) {
        dashboardData.tweetTypes.regular = parseFloat(typeMatch[1]);
        dashboardData.tweetTypes.replies = parseFloat(typeMatch[2]);
    } else {
        // Fallback to default values if not found
        dashboardData.tweetTypes.regular = 70;
        dashboardData.tweetTypes.replies = 30;
    }
    
    // Extract engagement data
    const likesMatch = summaryText.match(/Average likes: ([\d.]+)/);
    const retweetsMatch = summaryText.match(/Average retweets: ([\d.]+)/);
    const repliesMatch = summaryText.match(/Average replies: ([\d.]+)/);
    
    if (likesMatch) dashboardData.engagement.likes = parseFloat(likesMatch[1]);
    if (retweetsMatch) dashboardData.engagement.retweets = parseFloat(retweetsMatch[1]);
    if (repliesMatch) dashboardData.engagement.replies = parseFloat(repliesMatch[1]);
    
    // Extract topics
    let topicsSection = summaryText.match(/## (TOPICS|COMMON PHRASES)([\s\S]*?)(?=##|$)/);
    if (topicsSection && topicsSection[2]) {
        const topicLines = topicsSection[2].trim().split('\n');
        topicLines.forEach(line => {
            if (line.startsWith('-')) {
                const topic = line.replace(/^-\s+/, '').split(':')[0].trim();
                // Get count if available or assign default decreasing values
                let count = 10;
                const countMatch = line.match(/: (\d+)/);
                if (countMatch) count = parseInt(countMatch[1]);
                
                if (topic && dashboardData.topics.length < 8) {
                    dashboardData.topics.push(topic);
                    dashboardData.topicCounts.push(count);
                }
            }
        });
    }
    
    // Extract writing style insights
    let styleSection = summaryText.match(/## WRITING STYLE([\s\S]*?)(?=##|$)/);
    if (styleSection && styleSection[1]) {
        const styleLines = styleSection[1].trim().split('\n');
        styleLines.forEach(line => {
            if (line.startsWith('-') && dashboardData.styleInsights.length < 5) {
                dashboardData.styleInsights.push(line.replace(/^-\s+/, '').trim());
            }
        });
    }
    
    // Extract sample tweets (mock data, in a real implementation these would come from the backend)
    // In a full implementation, these would be fetched from the API or passed from the Flask template
    dashboardData.tweets = generateMockTweets();
}

/**
 * Generate mock tweet data for demonstration
 * In a real implementation, this would be replaced with actual tweet data
 */
function generateMockTweets() {
    const tweets = [];
    const now = new Date();
    
    // Create mock tweets with different characteristics
    for (let i = 0; i < 25; i++) {
        const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
        const sentiment = ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)];
        
        const topics = [];
        for (let j = 0; j < Math.floor(Math.random() * 3) + 1; j++) {
            if (dashboardData.topics.length > 0) {
                const randomIndex = Math.floor(Math.random() * dashboardData.topics.length);
                if (!topics.includes(dashboardData.topics[randomIndex])) {
                    topics.push(dashboardData.topics[randomIndex]);
                }
            }
        }
        
        tweets.push({
            id: `tweet-${i}`,
            date: date,
            text: `This is a sample tweet #${i+1} showing what the content might look like in the dashboard view.`,
            engagement: Math.floor(Math.random() * 100) + 5,
            sentiment: sentiment,
            topics: topics
        });
    }
    
    return tweets;
}

/**
 * Create sentiment distribution chart
 */
function createSentimentChart() {
    const ctx = document.getElementById('sentiment-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [
                    dashboardData.sentimentData.positive,
                    dashboardData.sentimentData.neutral,
                    dashboardData.sentimentData.negative
                ],
                backgroundColor: [
                    'rgba(25, 135, 84, 0.7)',
                    'rgba(108, 117, 125, 0.7)',
                    'rgba(220, 53, 69, 0.7)'
                ],
                borderColor: [
                    'rgb(25, 135, 84)',
                    'rgb(108, 117, 125)',
                    'rgb(220, 53, 69)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * Create tweet types distribution chart
 */
function createTweetTypesChart() {
    const ctx = document.getElementById('tweet-types-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Regular Tweets', 'Replies'],
            datasets: [{
                data: [
                    dashboardData.tweetTypes.regular,
                    dashboardData.tweetTypes.replies
                ],
                backgroundColor: [
                    'rgba(13, 110, 253, 0.7)',
                    'rgba(255, 193, 7, 0.7)'
                ],
                borderColor: [
                    'rgb(13, 110, 253)',
                    'rgb(255, 193, 7)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * Create engagement metrics chart
 */
function createEngagementChart() {
    const ctx = document.getElementById('engagement-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Likes', 'Retweets', 'Replies'],
            datasets: [{
                label: 'Average per Tweet',
                data: [
                    dashboardData.engagement.likes,
                    dashboardData.engagement.retweets,
                    dashboardData.engagement.replies
                ],
                backgroundColor: [
                    'rgba(220, 53, 69, 0.7)',
                    'rgba(25, 135, 84, 0.7)',
                    'rgba(13, 110, 253, 0.7)'
                ],
                borderColor: [
                    'rgb(220, 53, 69)',
                    'rgb(25, 135, 84)',
                    'rgb(13, 110, 253)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Create topics chart
 */
function createTopicsChart() {
    const ctx = document.getElementById('topics-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dashboardData.topics,
            datasets: [{
                label: 'Frequency',
                data: dashboardData.topicCounts,
                backgroundColor: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgb(13, 110, 253)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Setup writing style indicators
 */
function setupWritingStyleIndicators() {
    // Set formality and complexity values (these would be dynamically set in a real implementation)
    document.getElementById('formality-bar').style.width = '65%'; // Example value
    document.getElementById('complexity-bar').style.width = '45%'; // Example value
    
    // Add writing style insights
    const insightsList = document.getElementById('style-insights-list');
    if (insightsList) {
        dashboardData.styleInsights.forEach(insight => {
            const li = document.createElement('li');
            li.textContent = insight;
            insightsList.appendChild(li);
        });
        
        // If no insights were found, add a default message
        if (dashboardData.styleInsights.length === 0) {
            const li = document.createElement('li');
            li.textContent = "Primarily uses a conversational tone with a mix of questions and statements.";
            insightsList.appendChild(li);
            
            const li2 = document.createElement('li');
            li2.textContent = "Frequently employs personal anecdotes and first-person perspective.";
            insightsList.appendChild(li2);
        }
    }
}

/**
 * Setup tweet table with filtering and pagination
 */
function setupTweetTable() {
    // Populate the table initially
    renderTweetTable();
    
    // Setup filter buttons
    const filterButtons = document.querySelectorAll('.tweet-filters button');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Apply filter
            const filter = this.getAttribute('data-filter');
            applyTweetFilter(filter);
        });
    });
}

/**
 * Apply filter to tweet table
 */
function applyTweetFilter(filter) {
    let filteredTweets = [...dashboardData.tweets];
    
    // Apply filter
    switch(filter) {
        case 'positive':
            filteredTweets = filteredTweets.filter(tweet => tweet.sentiment === 'positive');
            break;
        case 'negative':
            filteredTweets = filteredTweets.filter(tweet => tweet.sentiment === 'negative');
            break;
        case 'high-engagement':
            filteredTweets.sort((a, b) => b.engagement - a.engagement);
            filteredTweets = filteredTweets.slice(0, Math.min(10, filteredTweets.length));
            break;
        // 'all' case does not filter
    }
    
    // Reset pagination to first page
    dashboardData.currentPage = 1;
    
    // Update table with filtered data
    renderTweetTable(filteredTweets);
}

/**
 * Render tweet table with pagination
 */
function renderTweetTable(filteredTweets = null) {
    const tweets = filteredTweets || dashboardData.tweets;
    const tableBody = document.getElementById('tweets-table-body');
    const paginationEl = document.getElementById('tweets-pagination');
    
    if (!tableBody || !paginationEl) return;
    
    // Clear existing content
    tableBody.innerHTML = '';
    paginationEl.innerHTML = '';
    
    // Calculate pagination
    const totalPages = Math.ceil(tweets.length / dashboardData.tweetsPerPage);
    const startIndex = (dashboardData.currentPage - 1) * dashboardData.tweetsPerPage;
    const endIndex = Math.min(startIndex + dashboardData.tweetsPerPage, tweets.length);
    
    // Add tweets to table
    for (let i = startIndex; i < endIndex; i++) {
        const tweet = tweets[i];
        
        const row = document.createElement('tr');
        
        // Format date
        const date = new Date(tweet.date);
        const formattedDate = date.toLocaleDateString() + '<br>' + 
            '<span class="text-muted small">' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) + '</span>';
        
        // Create sentiment badge
        const sentimentBadge = `<span class="sentiment-badge sentiment-${tweet.sentiment}">${tweet.sentiment}</span>`;
        
        // Create topic tags
        let topicTags = '';
        if (tweet.topics && tweet.topics.length > 0) {
            topicTags = tweet.topics.map(topic => `<span class="topic-tag">${topic}</span>`).join(' ');
        }
        
        row.innerHTML = `
            <td>${formattedDate}</td>
            <td>${tweet.text}</td>
            <td>${tweet.engagement}</td>
            <td>${sentimentBadge}</td>
            <td>${topicTags}</td>
        `;
        
        tableBody.appendChild(row);
    }
    
    // Create pagination controls
    renderPagination(totalPages, paginationEl);
}

/**
 * Render pagination controls
 */
function renderPagination(totalPages, paginationEl) {
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${dashboardData.currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" data-page="${dashboardData.currentPage - 1}">Previous</a>`;
    paginationEl.appendChild(prevLi);
    
    // Page number buttons
    let startPage = Math.max(1, dashboardData.currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    
    if (endPage - startPage < 4 && startPage > 1) {
        startPage = Math.max(1, endPage - 4);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageLi = document.createElement('li');
        pageLi.className = `page-item ${i === dashboardData.currentPage ? 'active' : ''}`;
        pageLi.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
        paginationEl.appendChild(pageLi);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${dashboardData.currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" data-page="${dashboardData.currentPage + 1}">Next</a>`;
    paginationEl.appendChild(nextLi);
    
    // Add event listeners to pagination links
    const pageLinks = paginationEl.querySelectorAll('.page-link');
    pageLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = parseInt(this.getAttribute('data-page'));
            
            // Only update if it's a valid page and not disabled
            if (!isNaN(page) && page >= 1 && page <= totalPages && !this.parentElement.classList.contains('disabled')) {
                dashboardData.currentPage = page;
                renderTweetTable();
            }
        });
    });
}

/**
 * Extract and display highlights from the summary
 */
function extractHighlights(summaryText) {
    const highlightsContainer = document.getElementById('summary-highlights');
    if (!highlightsContainer) return;
    
    // Look for key sections to extract highlights from
    const sections = [
        { name: 'Top Topics', regex: /## (TOPICS|COMMON PHRASES)([\s\S]*?)(?=##|$)/ },
        { name: 'Writing Style', regex: /## WRITING STYLE([\s\S]*?)(?=##|$)/ },
        { name: 'Engagement Insights', regex: /## ENGAGEMENT([\s\S]*?)(?=##|$)/ }
    ];
    
    let highlights = '';
    
    sections.forEach(section => {
        const match = summaryText.match(section.regex);
        if (match && match[2]) {
            highlights += `<div class="highlight-section mb-4">
                <h5>${section.name}</h5>
                <ul class="highlight-list">`;
            
            // Extract bullet points
            const points = match[2].split('\n')
                .filter(line => line.trim().startsWith('-'))
                .map(line => line.replace(/^-\s+/, '').trim())
                .slice(0, 3); // Show only top 3 points
                
            points.forEach(point => {
                highlights += `<li>${point}</li>`;
            });
            
            highlights += '</ul></div>';
        }
    });
    
    // If no highlights were found, add a default message
    if (!highlights) {
        highlights = `<div class="highlight-section">
            <p class="text-muted">View the full summary for detailed analysis insights.</p>
        </div>`;
    }
    
    highlightsContainer.innerHTML = highlights;
}