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
