from flask import Flask, render_template, jsonify, request, Response  # Import Response

import pandas as pd
import logging
import os
import feedparser

app = Flask(__name__, static_url_path='/static')

# Set up logging
logging.basicConfig(level=logging.DEBUG)


def load_stock_symbols():
    try:
        df = pd.read_excel('stock_names.xlsx')
        return df['Stock'].tolist()
    except Exception as e:
        app.logger.error(f"Error loading stock symbols: {str(e)}")
        return []


def load_industries():
    try:
        df = pd.read_excel('Stocks_top_Perf.xlsx')
        industries = df['Industry'].dropna().unique().tolist()
        return industries
    except Exception as e:
        app.logger.error(f"Error loading industries: {str(e)}")
        return []


def fetch_news_from_rss():
    feed_url = "https://economictimes.indiatimes.com/rssfeedsdefault.cms"  # Example RSS feed URL
    feed = feedparser.parse(feed_url)
    news_items = []
    for entry in feed.entries[:10]:  # Limit to the first 10 news items
        news_items.append({
            'title': entry.title,
            'link': entry.link
        })
    return news_items


stock_symbols = load_stock_symbols()


@app.route('/')
def index():
    response = Response(render_template('index.html', stock_symbols=stock_symbols))
    response.headers['x-content-type-options'] = 'nosniff'  # Adding x-content-type-options header
    return response


@app.route('/get_stock_symbols')
def get_stock_symbols():
    return jsonify(stock_symbols)


@app.route('/get_industries')
def get_industries():
    industries = load_industries()
    return jsonify(industries)


@app.route('/get_top_performers', methods=['GET'])
def get_top_performers():
    industry = request.args.get('industry')
    if not industry:
        return jsonify({'error': 'Industry not specified'}), 400

    excel_file_path = 'Stocks_top_Perf.xlsx'
    app.logger.info(f"Attempting to read Excel file from path: {os.path.abspath(excel_file_path)}")

    try:
        df = pd.read_excel(excel_file_path)
        industry_data = df[df['Industry'] == industry]
        top_performers = industry_data.nlargest(3, 'Return over 3years')[['Name', 'Return over 3years', 'Market Capitalization']]
        top_performers_dict = top_performers.to_dict(orient='records')
        return jsonify(top_performers_dict)
    except Exception as e:
        app.logger.error(f"Error fetching top performers data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/get_news_headlines', methods=['GET'])
def get_news_headlines():
    try:
        news_items = fetch_news_from_rss()
        response = jsonify(news_items)
        response.headers['x-content-type-options'] = 'nosniff'  # Adding x-content-type-options header
        return response
    except Exception as e:
        app.logger.error(f"Error fetching news headlines: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
