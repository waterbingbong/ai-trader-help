# Gemini 2.5 Integration for AI Trading Assistant

This document provides information about the Gemini 2.5 integration in the AI Trading Assistant, including how to use the new features and manage the knowledge base.

## Overview

The AI Trading Assistant now integrates Google's Gemini 2.5 AI model to enhance trading signals and analysis. This integration allows you to:

- Analyze trading data using advanced AI capabilities
- Add various media types (text, images, videos, files) to a knowledge base
- Use the knowledge base to improve trading insights
- Get AI-powered analysis of market conditions and trading opportunities

## Getting Started

### API Key

The system uses a Gemini API key for authentication. The key is currently set in the main script, but for security reasons, you can also set it as an environment variable:

```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

## Using Gemini Features

### Analyzing Trading Data

To analyze a trading symbol using Gemini 2.5:

```bash
python main.py ai analyze --symbol AAPL --days 30
```

This will:
1. Fetch the last 30 days of data for Apple stock
2. Process the data with technical indicators
3. Send the data to Gemini 2.5 for analysis
4. Display the AI-generated insights

You can adjust the number of days to analyze by changing the `--days` parameter.

### Managing the Knowledge Base

The knowledge base stores information that helps Gemini provide better trading insights. You can add various types of content:

#### Adding Content

**Adding Text:**

```bash
python main.py ai kb add --type text --content "Apple is planning to release a new iPhone in September, which could affect their stock price."
```

**Adding an Image (e.g., a chart):**

```bash
python main.py ai kb add --type image --content "path/to/chart.jpg" --category "charts"
```

**Adding a File:**

```bash
python main.py ai kb add --type file --content "path/to/analysis.pdf" --category "research"
```

#### Listing Knowledge Base Contents

To list all items in the knowledge base:

```bash
python main.py ai kb list
```

To list items in a specific category:

```bash
python main.py ai kb list --category "research"
```

#### Searching the Knowledge Base

To search for items containing specific keywords:

```bash
python main.py ai kb search --query "iPhone"
```

#### Deleting from the Knowledge Base

To delete a specific item:

```bash
python main.py ai kb delete --id "item_id_here"
```

To clear an entire category:

```bash
python main.py ai kb delete --category "charts"
```

## How It Works

### Integration Architecture

The Gemini integration consists of several components:

1. **GeminiIntegration**: Core class that handles API communication with Gemini 2.5
2. **KnowledgeBase**: Manages storage and retrieval of trading-related information
3. **MediaProcessor**: Processes different types of media (images, videos, files) for AI analysis

### Knowledge Base Structure

The knowledge base organizes information into categories:

- **market_data**: Historical price data and patterns
- **news**: Market news and events
- **analysis**: Trading analysis and reports
- **user_insights**: Custom insights provided by the user
- **images**: Charts, graphs, and other visual data
- **videos**: Video content related to trading
- **documents**: Research papers, reports, and other documents

### AI Analysis Process

When you request an analysis:

1. The system fetches and processes market data for the specified symbol
2. Technical indicators are calculated and normalized
3. The data is formatted and sent to Gemini 2.5 along with any relevant knowledge base items
4. Gemini analyzes the data and generates insights
5. The insights are presented to you in a readable format

## Best Practices

- Add relevant news, research, and analysis to the knowledge base regularly
- Include charts and technical analysis images for better visual pattern recognition
- Use specific categories to organize your knowledge base effectively
- Provide context when requesting analysis (e.g., mention recent events or concerns)
- Review and clean up the knowledge base periodically to maintain quality

## Limitations

- Video analysis capabilities are currently limited
- Very large files may not be processed efficiently
- The quality of insights depends on the quality of data and knowledge base content
- API rate limits may apply depending on your Gemini API usage tier

## Troubleshooting

- If you encounter API errors, verify your API key is correct
- For processing errors with media files, check that the file format is supported
- If the knowledge base becomes corrupted, you may need to clear categories and rebuild
- For performance issues, consider reducing the amount of data being processed at once