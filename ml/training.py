import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_PATH, VECTORIZER_PATH, DEFAULT_CATEGORIES

def preprocess_data(transactions):
    """
    Preprocess transaction data for model training.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        tuple: (X, y) preprocessed data and labels
    """
    descriptions = []
    categories = []
    
    for transaction in transactions:
        # Use the user-verified category if available, otherwise use original
        category = transaction.user_verified_category or transaction.original_category
        if not category:
            continue
            
        # Skip transactions without categories
        descriptions.append(transaction.description)
        categories.append(category)
    
    return descriptions, categories

def train_model(X, y):
    """
    Train a machine learning model for transaction categorization.
    
    Args:
        X: List of transaction descriptions
        y: List of transaction categories
        
    Returns:
        tuple: (vectorizer, model)
    """
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        analyzer='word',
        ngram_range=(1, 2),
        max_features=5000,
        stop_words='english'
    )
    
    # Create random forest classifier
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        random_state=42
    )
    
    # Prepare training data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Transform text data
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # Train model
    model.fit(X_train_vec, y_train)
    
    # Evaluate model
    predictions = model.predict(X_test_vec)
    print("Model Evaluation:")
    print(classification_report(y_test, predictions))
    
    # Calculate accuracy
    accuracy = np.mean(predictions == y_test)
    print(f"Accuracy: {accuracy:.4f}")
    
    return vectorizer, model

def save_model(vectorizer, model):
    """
    Save the trained model and vectorizer to disk.
    
    Args:
        vectorizer: The trained TF-IDF vectorizer
        model: The trained classification model
    """
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(model, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")
    print(f"Vectorizer saved to {VECTORIZER_PATH}")

def train_and_save_model(transactions):
    """
    Train and save a model using transaction data.
    
    Args:
        transactions: List of Transaction objects
        
    Returns:
        tuple: (vectorizer, model)
    """
    X, y = preprocess_data(transactions)
    
    if len(X) < 10:
        print("Not enough labeled data to train model. Need at least 10 labeled transactions.")
        return None, None
    
    vectorizer, model = train_model(X, y)
    save_model(vectorizer, model)
    
    return vectorizer, model

def train_from_labeled_csv(csv_path, column_mapping=None):
    """
    Train a model using a pre-labeled CSV file containing transaction data.
    
    Args:
        csv_path: Path to the CSV file with labeled transactions
        column_mapping: A dictionary mapping required columns to their names in the CSV
        
    Returns:
        tuple: (vectorizer, model) or (None, None) if training failed
    """
    from utils.csv_handler import validate_csv
    from config import DEFAULT_CSV_MAPPING
    
    if column_mapping is None:
        column_mapping = DEFAULT_CSV_MAPPING.copy()
    
    # Ensure the CSV has a category column
    if "category" not in column_mapping:
        print("Error: Column mapping must include a 'category' field")
        return None, None
    
    try:
        # Read the CSV file
        with open(csv_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Validate CSV
        valid, error_message, df = validate_csv(file_content, column_mapping)
        
        if not valid:
            print(f"Error validating CSV: {error_message}")
            return None, None
        
        # Check if category column exists
        if column_mapping["category"] not in df.columns:
            print(f"Error: Category column '{column_mapping['category']}' not found in CSV")
            return None, None
        
        # Extract descriptions and categories
        descriptions = df[column_mapping["description"]].fillna("").astype(str).tolist()
        categories = df[column_mapping["category"]].fillna("Miscellaneous").astype(str).tolist()
        
        # Check if we have enough data
        if len(descriptions) < 10:
            print("Not enough labeled data to train model. Need at least 10 labeled transactions.")
            return None, None
        
        # Train the model
        vectorizer, model = train_model(descriptions, categories)
        save_model(vectorizer, model)
        
        print(f"Model trained successfully using {len(descriptions)} labeled transactions")
        return vectorizer, model
        
    except Exception as e:
        print(f"Error training model from CSV: {str(e)}")
        return None, None
