/**
 * SocialScope-Tweets Visualization Module
 * Creates data visualizations for Twitter account analysis results
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the results page
    if (document.getElementById('summary-content')) {
        // Include Chart.js only when needed
        loadChartJS();
    }
});

/**
 * Load Chart.js and initialize visualizations
 */
function loadChartJS() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
    script.onload = initializeCharts;
    document.head.appendChild(script);
}

/**
 * Initialize all charts after Chart.js is loaded
 */
function initializeCharts() {
    const chartData = extractChartData();
    
    // Create sentiment chart if element exists
    if (document.getElementById('sentiment-chart')) {
        createSentimentChart('sentiment-chart', 
                           chartData.positive, 
                           chartData.neutral, 
                           chartData.negative);
    }
    
    // Create topics chart if element exists and we have topics
    if (document.getElementById('topics-chart') && chartData.topics.length > 0) {
        createTopicsChart('topics-chart', chartData.topics, chartData.topicCounts);
    }
}

/**
 * Parse summary text to extract data for charts
 */
function extractChartData() {
    const summaryText = document.getElementById('summary-content').textContent;
    const data = {
        positive: 0,
        neutral: 0,
        negative: 0,
        topics: [],
        topicCounts: []
    };
    
    // Extract sentiment percentages
    const sentimentMatch = summaryText.match(/Positive: ([\d.]+)%\s+Neutral: ([\d.]+)%\s+Negative: ([\d.]+)%/);
    
    if (sentimentMatch && sentimentMatch.length >= 4) {
        data.positive = parseFloat(sentimentMatch[1]);
        data.neutral = parseFloat(sentimentMatch[2]);
        data.negative = parseFloat(sentimentMatch[3]);
    }
    
    // Extract topics - look for ## COMMON PHRASES or ## VOCABULARY sections
    let topicsSection = summaryText.match(/## COMMON PHRASES([\s\S]*?)(?=##|$)/);
    
    if (!topicsSection) {
        topicsSection = summaryText.match(/## VOCABULARY([\s\S]*?)Most frequent words:([\s\S]*?)(?=##|$)/);
        if (topicsSection) {
            topicsSection = topicsSection[2]; // Use the second capture group for most frequent words
        }
    } else {
        topicsSection = topicsSection[1];
    }
    
    if (topicsSection) {
        const lines = topicsSection.trim().split('\n');
        lines.forEach((line, index) => {
            if (line.startsWith('-')) {
                // Extract the topic name, handling different formats
                let topic = '';
                let count = 10 - index; // Default count based on position
                
                if (line.includes(': ')) {
                    // Format: "- word: count times"
                    const parts = line.replace(/^-\s+/, '').split(': ');
                    topic = parts[0].trim();
                    if (parts[1] && parts[1].match(/\d+/)) {
                        count = parseInt(parts[1].match(/\d+/)[0]);
                    }
                } else if (line.match(/^-\s+"([^"]+)"/)) {
                    // Format: "- "phrase""
                    topic = line.match(/^-\s+"([^"]+)"/)[1];
                } else {
                    // Format: "- topic"
                    topic = line.replace(/^-\s+/, '').trim();
                }
                
                if (topic) {
                    data.topics.push(topic);
                    data.topicCounts.push(count);
                }
                
                // Limit to top 5
                if (data.topics.length >= 5) {
                    return false; // Break the loop
                }
            }
        });
    }
    
    return data;
}

/**
 * Create a bar chart for sentiment distribution
 */
function createSentimentChart(elementId, positive, neutral, negative) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Create a bar chart for sentiment distribution
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                label: 'Sentiment Distribution',
                data: [positive, neutral, negative],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(201, 203, 207, 0.6)',
                    'rgba(255, 99, 132, 0.6)'
                ],
                borderColor: [
                    'rgb(75, 192, 192)',
                    'rgb(201, 203, 207)',
                    'rgb(255, 99, 132)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                },
                title: {
                    display: true,
                    text: 'Tweet Sentiment Analysis'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                }
            }
        }
    });
}

/**
 * Create a horizontal bar chart for topics
 */
function createTopicsChart(elementId, topics, counts) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Create a horizontal bar chart for topics
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topics,
            datasets: [{
                label: 'Topic Mentions',
                data: counts,
                backgroundColor: 'rgba(54, 162, 235, 0.6)',
                borderColor: 'rgb(54, 162, 235)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            plugins: {
                legend: {
                    display: false,
                },
                title: {
                    display: true,
                    text: 'Most Mentioned Topics'
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                }
            }
        }
    });
}