# ToTheMoon - Personal Finance Tracker

Little private finance tracker to upload bank transaction data, automatically categorize transactions using ML, and visualize spending trends.

## Features

- CSV upload and parsing for bank transactions
- AI/ML-powered transaction categorization
- Manual verification and override of categories
- Interactive data visualization dashboard
- Integration with Notion databases

## Setup Instructions

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python run.py
   ```
   or
   ```
   python run.py run
   ```

## Usage

1. Upload your bank transaction CSV file
2. Review and verify AI-suggested transaction categories
3. View spending visualizations and insights
4. Optionally retrain the model with your verified data

## Notion Integration

ToTheMoon can now sync your financial data with a Notion database:

1. Create a Notion integration at [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a database in Notion with the required properties (Date, Description, Amount, Category)
3. Share your database with your integration
4. In ToTheMoon, go to the "Notion Integration" page to set up the connection
5. Once configured, you can push transaction data to Notion directly from the app

You can also use the command line to push data to Notion:
```
# Push all transactions
python run.py notion

# Push only the most recent 10 transactions
python run.py notion --last 10
```
